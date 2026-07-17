from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from accounts.models import User
from accounts.permissions import IsElectionViewer, IsElectionManager
from elections.models import Election, VoterEligibility, VoterRegister, VoterCategory
from elections.serializers import VoterEligibilitySerializer
from elections.services.eligibility import resolve_or_create_voter
from elections.services.register_service import (
    import_register_csv,
    sync_eligibility_from_registers,
    user_is_on_election_register,
)


class EligibilityListCreateView(generics.ListCreateAPIView):
    serializer_class = VoterEligibilitySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsElectionViewer()]
        return [IsElectionManager()]

    def get_queryset(self):
        election = get_object_or_404(Election, uuid=self.kwargs['election_uuid'])
        return VoterEligibility.objects.filter(
            election=election,
            is_eligible=True,
        ).select_related(
            'user', 'user__faculty', 'user__department', 'verified_by',
        )

    def list(self, request, *args, **kwargs):
        election = get_object_or_404(Election, uuid=self.kwargs['election_uuid'])
        if election.register_id or election.registers.exists():
            sync_eligibility_from_registers(election, verified_by=None)
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        election = get_object_or_404(Election, uuid=self.kwargs['election_uuid'])

        identifier = (
            request.data.get('user_identifier')
            or request.data.get('index_number')
            or ''
        ).strip()
        user = None
        if request.data.get('user_uuid'):
            user = User.objects.filter(uuid=request.data.get('user_uuid')).first()
        elif identifier:
            user, err = resolve_or_create_voter(identifier)
            if err:
                return Response({'user_identifier': [err]}, status=status.HTTP_400_BAD_REQUEST)

        if user and (election.register_id or election.registers.exists()) and not user_is_on_election_register(user, election):
            return Response(
                {
                    'error': (
                        'This student is not on any voter register for this election. '
                        'Import them into a register category first.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(election=election, verified_by=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class EligibilityDeleteView(generics.DestroyAPIView):
    permission_classes = [IsElectionManager]
    lookup_field = 'uuid'

    def get_queryset(self):
        election = get_object_or_404(Election, uuid=self.kwargs['election_uuid'])
        return VoterEligibility.objects.filter(election=election)


class EligibilityBulkImportView(APIView):
    """
    Import voters into a register category, then sync eligibility.
    Requires register_uuid + category_uuid + CSV file.
    """
    permission_classes = [IsElectionManager]

    def post(self, request, election_uuid):
        election = get_object_or_404(Election, uuid=election_uuid)
        register_uuid = request.data.get('register_uuid')
        category_uuid = request.data.get('category_uuid')
        file_obj = request.FILES.get('file')

        if not register_uuid or not category_uuid:
            return Response(
                {
                    'error': (
                        'register_uuid and category_uuid are required. '
                        'Import voters into a register category, not directly onto eligibility.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        register = get_object_or_404(VoterRegister, uuid=register_uuid, election=election)
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
                'created': record.rows_created,
                'processed': record.rows_processed,
                'errors': record.errors,
                'register_uuid': str(register.uuid),
                'category_uuid': str(category.uuid),
            },
            status=status.HTTP_201_CREATED,
        )
