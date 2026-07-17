from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from accounts.permissions import (
    IsAdmin,
    IsMainEC,
    IsSubEC,
    IsMainECOrSubEC,
    IsElectionViewer,
    IsElectionMonitorViewer,
)
from accounts.governance import (
    GovernanceBlocked,
    assert_institution_ready,
    decision_submitted_response,
    governance_applies_to_user,
    submit_main_ec_decision,
)
from accounts.models import MainECDecision
from accounts.org import user_is_main_ec, user_is_sub_ec
from elections.models import Election, Position
from elections.serializers import (
    ElectionSerializer, ElectionCreateUpdateSerializer,
    PositionSerializer
)
from elections.services.deletion import delete_election
from elections.services.ec_access import (
    ElectionAccessBlocked,
    assert_can_manage_election,
    elections_visible_to,
    resolve_create_owner,
    user_can_manage_election,
)


def _manage_or_403(user, election):
    try:
        assert_can_manage_election(user, election)
        return None
    except ElectionAccessBlocked as exc:
        return Response(
            {'detail': str(exc), 'code': exc.code},
            status=status.HTTP_403_FORBIDDEN,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ELECTION CRUD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ElectionListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsElectionViewer()]
        return [IsMainECOrSubEC()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ElectionCreateUpdateSerializer
        return ElectionSerializer

    def get_queryset(self):
        return elections_visible_to(self.request.user).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        # Dual approval only for Main EC institutional elections
        if user_is_main_ec(request.user) and not user_is_sub_ec(request.user) and governance_applies_to_user(request.user):
            try:
                assert_institution_ready(request.user)
                owner = resolve_create_owner(request.user)
            except (GovernanceBlocked, ElectionAccessBlocked) as exc:
                code = getattr(exc, 'code', 'forbidden')
                return Response({'detail': str(exc), 'code': code}, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            title = serializer.validated_data.get('title') or 'New election'
            decision = submit_main_ec_decision(
                user=request.user,
                decision_type=MainECDecision.TYPE_ELECTION_CREATE,
                title=f'Create election: {title}',
                summary=(
                    'Create an institutional election. Enrolls only after both '
                    'Main EC members approve.'
                ),
                payload={
                    'election': request.data,
                    'owner_type': owner['owner_type'],
                    'institution_uuid': str(owner['institution'].uuid),
                    'owner_ec_unit_uuid': str(owner['owner_ec_unit'].uuid) if owner.get('owner_ec_unit') else None,
                },
            )
            return decision_submitted_response(decision)

        # Sub EC creates immediately (no Main dual-approval gate)
        try:
            resolve_create_owner(request.user)
        except ElectionAccessBlocked as exc:
            return Response({'detail': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        owner = resolve_create_owner(self.request.user)
        serializer.save(created_by=self.request.user, **owner)


class ElectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'uuid'

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [IsElectionViewer()]
        return [IsMainECOrSubEC()]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ElectionCreateUpdateSerializer
        return ElectionSerializer

    def get_queryset(self):
        return elections_visible_to(self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        blocked = _manage_or_403(request.user, instance)
        if blocked:
            return blocked

        if (
            user_is_main_ec(request.user)
            and not user_is_sub_ec(request.user)
            and governance_applies_to_user(request.user)
            and instance.owner_type == Election.OWNER_MAIN
        ):
            try:
                assert_institution_ready(request.user)
            except GovernanceBlocked as exc:
                return Response({'detail': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)

            partial = kwargs.pop('partial', False)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            decision = submit_main_ec_decision(
                user=request.user,
                decision_type=MainECDecision.TYPE_ELECTION_UPDATE,
                title=f'Update election: {instance.title}',
                summary='Update election settings. Enrolls only after both Main EC members approve.',
                payload={
                    'election_uuid': str(instance.uuid),
                    'election': request.data,
                },
            )
            return decision_submitted_response(decision)

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        blocked = _manage_or_403(request.user, instance)
        if blocked:
            return blocked

        if (
            user_is_main_ec(request.user)
            and not user_is_sub_ec(request.user)
            and governance_applies_to_user(request.user)
            and instance.owner_type == Election.OWNER_MAIN
        ):
            try:
                assert_institution_ready(request.user)
            except GovernanceBlocked as exc:
                return Response({'detail': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)

            decision = submit_main_ec_decision(
                user=request.user,
                decision_type=MainECDecision.TYPE_ELECTION_DELETE,
                title=f'Delete election: {instance.title}',
                summary='Permanently delete this election after dual Main EC approval.',
                payload={'election_uuid': str(instance.uuid)},
            )
            return decision_submitted_response(decision)

        return super().destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        delete_election(instance)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# POSITIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PositionListCreateView(generics.ListCreateAPIView):
    serializer_class = PositionSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsElectionViewer()]
        return [IsMainECOrSubEC()]

    def _election(self):
        return get_object_or_404(elections_visible_to(self.request.user), uuid=self.kwargs['uuid'])

    def get_queryset(self):
        election = self._election()
        return (
            Position.objects.filter(election=election)
            .prefetch_related('restricted_categories__register')
            .order_by('display_order')
        )

    def create(self, request, *args, **kwargs):
        election = self._election()
        blocked = _manage_or_403(request.user, election)
        if blocked:
            return blocked
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        election = self._election()
        if (
            user_is_main_ec(self.request.user)
            and not user_is_sub_ec(self.request.user)
            and governance_applies_to_user(self.request.user)
        ):
            assert_institution_ready(self.request.user)
        serializer.save(election=election)


class PositionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PositionSerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'position_uuid'

    def get_permissions(self):
        if self.request.method in ('GET', 'HEAD', 'OPTIONS'):
            return [IsElectionViewer()]
        return [IsMainECOrSubEC()]

    def _election(self):
        return get_object_or_404(elections_visible_to(self.request.user), uuid=self.kwargs['uuid'])

    def get_queryset(self):
        election = self._election()
        return (
            Position.objects.filter(election=election)
            .prefetch_related('restricted_categories__register')
        )

    def update(self, request, *args, **kwargs):
        blocked = _manage_or_403(request.user, self._election())
        if blocked:
            return blocked
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        blocked = _manage_or_403(request.user, self._election())
        if blocked:
            return blocked
        return super().destroy(request, *args, **kwargs)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ELECTION ACTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class OpenElectionView(APIView):
    permission_classes = [IsMainECOrSubEC]

    def post(self, request, uuid):
        election = get_object_or_404(elections_visible_to(request.user), uuid=uuid)
        blocked = _manage_or_403(request.user, election)
        if blocked:
            return blocked

        if election.status != 'scheduled':
            return Response({'error': 'Election must be scheduled before opening'}, status=status.HTTP_400_BAD_REQUEST)

        if (
            user_is_main_ec(request.user)
            and not user_is_sub_ec(request.user)
            and governance_applies_to_user(request.user)
            and election.owner_type == Election.OWNER_MAIN
        ):
            try:
                assert_institution_ready(request.user)
            except GovernanceBlocked as exc:
                return Response({'detail': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
            decision = submit_main_ec_decision(
                user=request.user,
                decision_type=MainECDecision.TYPE_ELECTION_OPEN,
                title=f'Open election: {election.title}',
                summary='Open voting. Enrolls only after both Main EC members approve.',
                payload={'election_uuid': str(election.uuid)},
            )
            return decision_submitted_response(decision)

        from elections.services.register_service import sync_eligibility_from_registers

        synced = sync_eligibility_from_registers(election, verified_by=request.user)
        election.status = 'open'
        election.save(update_fields=['status', 'updated_at'])
        return Response({
            'message': 'Election opened successfully',
            'eligibility_synced': synced,
        })


class CloseElectionView(APIView):
    permission_classes = [IsMainECOrSubEC]

    def post(self, request, uuid):
        election = get_object_or_404(elections_visible_to(request.user), uuid=uuid)
        blocked = _manage_or_403(request.user, election)
        if blocked:
            return blocked

        if election.status not in ['open', 'paused']:
            return Response({'error': 'Election must be open or paused to close'}, status=status.HTTP_400_BAD_REQUEST)

        if (
            user_is_main_ec(request.user)
            and not user_is_sub_ec(request.user)
            and governance_applies_to_user(request.user)
            and election.owner_type == Election.OWNER_MAIN
        ):
            try:
                assert_institution_ready(request.user)
            except GovernanceBlocked as exc:
                return Response({'detail': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
            decision = submit_main_ec_decision(
                user=request.user,
                decision_type=MainECDecision.TYPE_ELECTION_CLOSE,
                title=f'Close election: {election.title}',
                summary='Close voting. Enrolls only after both Main EC members approve.',
                payload={'election_uuid': str(election.uuid)},
            )
            return decision_submitted_response(decision)

        election.status = 'closed'
        election.save()
        return Response({'message': 'Election closed successfully'})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ELECTION MONITOR – ADMIN AND AUDITOR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ElectionMonitorView(APIView):
    permission_classes = [IsElectionMonitorViewer]

    def get(self, request, uuid):
        # Sub EC monitor: only their own elections. Main/auditor: visible set.
        from accounts.permissions import get_role_name
        role = get_role_name(request.user)
        if role == 'auditor' or user_is_main_ec(request.user):
            election = get_object_or_404(elections_visible_to(request.user), uuid=uuid)
        elif user_is_sub_ec(request.user):
            election = get_object_or_404(elections_visible_to(request.user), uuid=uuid)
        else:
            election = get_object_or_404(Election, uuid=uuid)
        from elections.monitor_service import get_election_monitor_data
        data = get_election_monitor_data(election)
        data['can_manage'] = user_can_manage_election(request.user, election)
        return Response(data)
