"""Voter register CRUD, categories, entries, and CSV import."""

from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsElectionManager, IsElectionViewer
from elections.models import (
    Election,
    VoterCategory,
    VoterRegister,
    VoterRegisterEntry,
)
from elections.serializers import (
    VoterCategorySerializer,
    VoterRegisterEntrySerializer,
    VoterRegisterSerializer,
    VoterRegisterWriteSerializer,
)
from elections.services.register_service import import_register_csv, sync_eligibility_from_registers


def _election(kwargs):
    return get_object_or_404(Election, uuid=kwargs['election_uuid'])


def _register(kwargs):
    """Resolve a register owned by the election, or linked as its primary register."""
    election = _election(kwargs)
    register = get_object_or_404(VoterRegister, uuid=kwargs['register_uuid'])
    if register.election_id != election.id and election.register_id != register.pk:
        raise Http404('No VoterRegister matches the given query.')
    return register


class AvailableRegisterListView(generics.ListAPIView):
    """Registers that can be selected as an election's primary register."""
    serializer_class = VoterRegisterSerializer
    permission_classes = [IsElectionViewer]

    def get_queryset(self):
        from accounts.governance import resolve_user_institution
        from accounts.org import user_is_main_ec, user_is_sub_ec
        from elections.services.ec_access import (
            register_matches_sub_ec_scope,
            user_sub_ec_units,
        )

        institution = resolve_user_institution(self.request.user)
        # One live institutional register only — never offer election-owned clones
        # (those caused duplicate counts like 660 vs 50 for the "same" list).
        qs = (
            VoterRegister.objects.filter(
                institution__isnull=False,
                replace_of__isnull=True,
                approval_status=VoterRegister.APPROVAL_APPROVED,
            )
            .prefetch_related('categories', 'entries')
            .select_related('institution')
            .order_by('name')
        )
        if institution:
            qs = qs.filter(institution=institution)
        elif user_is_main_ec(self.request.user) or user_is_sub_ec(self.request.user):
            return qs.none()

        # Sub EC only sees Sub-scoped registers that intersect their assignments.
        if user_is_sub_ec(self.request.user) and not user_is_main_ec(self.request.user):
            units = user_sub_ec_units(self.request.user)
            if not units:
                return qs.none()
            qs = qs.filter(audience=VoterRegister.AUDIENCE_SUB)
            allowed_ids = [
                r.pk for r in qs
                if any(register_matches_sub_ec_scope(r, unit) for unit in units)
            ]
            return qs.filter(pk__in=allowed_ids)

        # Main EC institutional elections: only Main EC / institution categories.
        # Never offer faculty/department registers that belong to Sub EC scopes.
        if user_is_main_ec(self.request.user):
            return qs.filter(audience=VoterRegister.AUDIENCE_MAIN)

        return qs


class RegisterListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsElectionViewer()]
        return [IsElectionManager()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VoterRegisterWriteSerializer
        return VoterRegisterSerializer

    def get_queryset(self):
        election = _election(self.kwargs)
        owned = Q(election=election)
        if election.register_id:
            owned = owned | Q(pk=election.register_id)
        return (
            VoterRegister.objects.filter(owned)
            .prefetch_related('categories', 'entries')
            .distinct()
            .order_by('name')
        )

    def perform_create(self, serializer):
        election = _election(self.kwargs)
        register = serializer.save(election=election)
        if not election.register_id:
            election.register = register
            election.save(update_fields=['register', 'updated_at'])


class RegisterDetailView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'uuid'
    lookup_url_kwarg = 'register_uuid'

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsElectionViewer()]
        return [IsElectionManager()]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return VoterRegisterWriteSerializer
        return VoterRegisterSerializer

    def get_queryset(self):
        election = _election(self.kwargs)
        owned = Q(election=election)
        if election.register_id:
            owned = owned | Q(pk=election.register_id)
        return (
            VoterRegister.objects.filter(owned)
            .prefetch_related('categories', 'entries')
            .distinct()
        )

    def perform_destroy(self, instance):
        election = _election(self.kwargs)
        # Shared (linked) register: unlink only — do not delete the source roll.
        if instance.election_id != election.id:
            if election.register_id == instance.pk:
                election.register = None
                election.save(update_fields=['register', 'updated_at'])
                sync_eligibility_from_registers(election, verified_by=self.request.user)
            return

        if election and election.register_id == instance.pk:
            election.register = None
            election.save(update_fields=['register', 'updated_at'])
        # Clear primary links from any elections that shared this register.
        Election.objects.filter(register=instance).update(register=None)
        instance.delete()
        sync_eligibility_from_registers(election, verified_by=self.request.user)


class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = VoterCategorySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsElectionViewer()]
        return [IsElectionManager()]

    def get_queryset(self):
        register = _register(self.kwargs)
        return VoterCategory.objects.filter(register=register).order_by('name')

    def perform_create(self, serializer):
        register = _register(self.kwargs)
        serializer.save(register=register)


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VoterCategorySerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'category_uuid'

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsElectionViewer()]
        return [IsElectionManager()]

    def get_queryset(self):
        register = _register(self.kwargs)
        return VoterCategory.objects.filter(register=register)


class RegisterEntryListView(generics.ListAPIView):
    serializer_class = VoterRegisterEntrySerializer
    permission_classes = [IsElectionViewer]

    def get_queryset(self):
        register = _register(self.kwargs)
        qs = (
            VoterRegisterEntry.objects.filter(register=register)
            .select_related('category', 'user', 'user__faculty', 'user__department')
            .order_by('voter_id')
        )
        category_uuid = self.request.query_params.get('category')
        if category_uuid:
            qs = qs.filter(category__uuid=category_uuid)
        search = (self.request.query_params.get('search') or '').strip()
        if search:
            qs = qs.filter(Q(voter_id__icontains=search) | Q(full_name__icontains=search))
        return qs


class RegisterImportView(APIView):
    permission_classes = [IsElectionManager]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, election_uuid, register_uuid):
        register = _register({'election_uuid': election_uuid, 'register_uuid': register_uuid})
        category_uuid = request.data.get('category_uuid')
        file_obj = request.FILES.get('file')
        if not category_uuid:
            return Response({'error': 'category_uuid is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not file_obj:
            return Response({'error': 'CSV file is required'}, status=status.HTTP_400_BAD_REQUEST)

        category = get_object_or_404(VoterCategory, uuid=category_uuid, register=register)
        try:
            record = import_register_csv(
                register=register,
                category=category,
                file_obj=file_obj,
                imported_by=request.user,
            )
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                'uuid': str(record.uuid),
                'file_name': record.file_name,
                'rows_processed': record.rows_processed,
                'rows_created': record.rows_created,
                'errors': record.errors,
                'category': {'uuid': str(category.uuid), 'name': category.name},
            },
            status=status.HTTP_201_CREATED,
        )
