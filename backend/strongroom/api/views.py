from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.permissions import IsStrongroomViewer, IsAdmin, IsStrongroomAdmin
from elections.models import Election
from strongroom.models import (
    ElectionSeal, BallotSeal, CustodyRecord,
    StrongroomCommittee, StrongroomCommitteeMember,
)
from strongroom.serializers import (
    StrongroomElectionDetailSerializer,
    StrongroomCommitteeSerializer,
    CommitteeOverviewSerializer,
    election_has_approved_committee,
    has_any_approved_committee,
)
from accounts.models import User
from accounts.org import user_is_main_ec, user_is_sub_ec
from strongroom.services import (
    create_vault_session,
    get_active_session,
    close_vault_session,
    request_election_access,
    log_seal_reveal,
    VAULT_SESSION_TTL_MINUTES,
)
from strongroom.committee_service import (
    CommitteeError,
    nominate_committee,
    approve_committee,
    start_unlock_challenge,
    confirm_unlock_peer,
    complete_unlock_with_nominee_key,
    active_unlock_for_viewer,
    serialize_challenge,
)


def _vault_token(request):
    return request.headers.get('X-Vault-Token') or request.data.get('vault_token')


def _committee_required_response(message=None):
    return Response(
        {
            'error': message or 'Custody vault opens only after a strongroom committee is approved for this election',
            'code': 'committee_required',
        },
        status=status.HTTP_403_FORBIDDEN,
    )


class CommitteeOverviewView(APIView):
    """List elections with committee status — no vault session required."""
    permission_classes = [IsStrongroomViewer]

    def get(self, request):
        from accounts.org import user_is_main_ec, user_is_sub_ec
        elections = Election.objects.all().order_by('-created_at')
        peers = (
            User.objects.filter(is_active=True)
            .exclude(pk=request.user.pk)
            .select_related('role')
        )
        peer_options = []
        for u in peers:
            if user_is_main_ec(u) or user_is_sub_ec(u):
                peer_options.append({
                    'uuid': str(u.uuid),
                    'email': u.email,
                    'name': u.get_full_name() or u.email,
                    'is_main_ec': user_is_main_ec(u),
                    'is_sub_ec': user_is_sub_ec(u),
                })
        return Response({
            'has_approved_committee': has_any_approved_committee(),
            'elections': CommitteeOverviewSerializer(elections, many=True).data,
            'peer_ec_options': peer_options,
        })


class VaultAuthenticateView(APIView):
    """
    EC: step 1 of 3-party unlock (peer confirm + nominee key).
    Auditor: password step-up only (seal inspection; still no Super Admin).
    """
    permission_classes = [IsStrongroomViewer]

    def post(self, request):
        from accounts.permissions import is_auditor, is_admin
        from accounts.org import user_is_main_ec, user_is_sub_ec

        password = request.data.get('password', '')
        if not password:
            return Response({'error': 'Password required'}, status=status.HTTP_400_BAD_REQUEST)

        is_ec = is_admin(request.user) or user_is_main_ec(request.user) or user_is_sub_ec(request.user)
        if is_auditor(request.user) and not is_ec:
            if not has_any_approved_committee():
                return _committee_required_response(
                    'Vault opens after a custody committee is approved for at least one election'
                )
            if not request.user.check_password(password):
                return Response({'error': 'Invalid credentials', 'code': 'invalid_credentials'}, status=status.HTTP_403_FORBIDDEN)
            token, session = create_vault_session(request.user, request)
            return Response({
                'vault_token': token,
                'session_uuid': str(session.uuid),
                'expires_at': session.expires_at.isoformat(),
                'ttl_minutes': VAULT_SESSION_TTL_MINUTES,
                'message': 'Vault access granted',
            })

        try:
            election = None
            election_uuid = request.data.get('election_uuid')
            if election_uuid:
                election = get_object_or_404(Election, uuid=election_uuid)
            payload = start_unlock_challenge(
                actor=request.user,
                password=password,
                election=election,
            )
            return Response(payload)
        except CommitteeError as exc:
            return Response({'error': exc.message, 'code': exc.code}, status=exc.status)


class VaultUnlockStatusView(APIView):
    permission_classes = [IsStrongroomViewer]

    def get(self, request):
        challenge = active_unlock_for_viewer(request.user)
        if not challenge:
            return Response({'active': False})
        return Response({'active': True, 'challenge': serialize_challenge(challenge, request.user)})


class VaultUnlockPeerConfirmView(APIView):
    permission_classes = [IsStrongroomViewer]

    def post(self, request):
        try:
            payload = confirm_unlock_peer(
                actor=request.user,
                challenge_uuid=request.data.get('challenge_uuid'),
            )
            return Response(payload)
        except CommitteeError as exc:
            return Response({'error': exc.message, 'code': exc.code}, status=exc.status)


class VaultUnlockNomineeKeyView(APIView):
    permission_classes = [IsStrongroomViewer]

    def post(self, request):
        try:
            payload = complete_unlock_with_nominee_key(
                actor=request.user,
                challenge_uuid=request.data.get('challenge_uuid'),
                nominee_key=request.data.get('nominee_key') or request.data.get('key') or '',
                request=request,
            )
            return Response(payload)
        except CommitteeError as exc:
            return Response({'error': exc.message, 'code': exc.code}, status=exc.status)


class VaultSessionStatusView(APIView):
    permission_classes = [IsStrongroomViewer]

    def get(self, request):
        vault_token = _vault_token(request)
        session = get_active_session(request.user, vault_token)
        if not session:
            return Response({'active': False}, status=status.HTTP_200_OK)

        remaining = int((session.expires_at - timezone.now()).total_seconds())
        return Response({
            'active': True,
            'session_uuid': str(session.uuid),
            'expires_at': session.expires_at.isoformat(),
            'remaining_seconds': max(0, remaining),
            'ip_address': session.ip_address,
        })


class VaultSessionCloseView(APIView):
    permission_classes = [IsStrongroomViewer]

    def post(self, request):
        vault_token = _vault_token(request)
        session = get_active_session(request.user, vault_token)
        if session:
            close_vault_session(session, request.user, reason='manual')
        return Response({'message': 'Vault session closed'})


class RequiresVaultSessionMixin:
    def check_vault_session(self, request):
        vault_token = _vault_token(request)
        session = get_active_session(request.user, vault_token)
        if not session:
            return None, Response(
                {'error': 'Vault session required', 'code': 'vault_session_required'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return session, None


class StrongroomElectionListView(RequiresVaultSessionMixin, generics.ListAPIView):
    permission_classes = [IsStrongroomViewer]
    serializer_class = StrongroomElectionDetailSerializer
    queryset = Election.objects.all().order_by('-created_at')

    def list(self, request, *args, **kwargs):
        _, error = self.check_vault_session(request)
        if error:
            return error
        return super().list(request, *args, **kwargs)


class StrongroomElectionDetailView(RequiresVaultSessionMixin, generics.RetrieveAPIView):
    permission_classes = [IsStrongroomViewer]
    serializer_class = StrongroomElectionDetailSerializer
    lookup_field = 'uuid'
    queryset = Election.objects.all()

    def retrieve(self, request, *args, **kwargs):
        _, error = self.check_vault_session(request)
        if error:
            return error
        election = self.get_object()
        if not election_has_approved_committee(election):
            return _committee_required_response()
        return super().retrieve(request, *args, **kwargs)


class ElectionVaultAccessView(RequiresVaultSessionMixin, APIView):
    permission_classes = [IsStrongroomViewer]

    def post(self, request, uuid):
        _, error = self.check_vault_session(request)
        if error:
            return error

        election = get_object_or_404(Election, uuid=uuid)
        if not election_has_approved_committee(election):
            return _committee_required_response()

        reason = (request.data.get('reason') or '').strip()
        if len(reason) < 10:
            return Response(
                {'error': 'Provide a reason (at least 10 characters) for vault access'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_request, vault_session = request_election_access(election, request.user, reason)
        return Response({
            'message': 'Election vault access granted',
            'access_request_uuid': str(access_request.uuid),
            'vault_session_uuid': str(vault_session.uuid),
        })


class RevealSealView(RequiresVaultSessionMixin, APIView):
    permission_classes = [IsStrongroomViewer]

    def post(self, request, uuid):
        _, error = self.check_vault_session(request)
        if error:
            return error

        election = get_object_or_404(Election, uuid=uuid)
        if not election_has_approved_committee(election):
            return _committee_required_response()

        seal_type = request.data.get('seal_type')
        seal_uuid = request.data.get('seal_uuid')

        if seal_type == 'election':
            seal = get_object_or_404(ElectionSeal, uuid=seal_uuid, election=election)
        elif seal_type == 'ballot':
            seal = get_object_or_404(BallotSeal, uuid=seal_uuid, election=election)
        else:
            return Response({'error': 'Invalid seal_type'}, status=status.HTTP_400_BAD_REQUEST)

        log_seal_reveal(election, request.user, seal_type, seal.uuid, seal.seal_hash)
        return Response({
            'seal_hash': seal.seal_hash,
            'seal_type': seal_type,
            'status': seal.status,
            'revealed_at': timezone.now().isoformat(),
        })


class LockElectionView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        CustodyRecord.objects.create(
            election=election,
            action='election_locked',
            actor=request.user,
            metadata={'timestamp': timezone.now().isoformat()},
        )
        return Response({'message': 'Election locked successfully'})


class NominateCommitteeView(APIView):
    """EC nominates a 3-person custody committee: self + peer EC + candidate nominee."""
    permission_classes = [IsStrongroomAdmin]

    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        try:
            committee = nominate_committee(
                election=election,
                actor=request.user,
                peer_ec_uuid=request.data.get('peer_ec_uuid'),
                nominee_full_name=request.data.get('nominee_full_name') or '',
                nominee_phone=request.data.get('nominee_phone') or '',
                nominee_email=request.data.get('nominee_email') or '',
            )
        except CommitteeError as exc:
            return Response({'error': exc.message, 'code': exc.code}, status=exc.status)

        committee = StrongroomCommittee.objects.prefetch_related('members__user').get(pk=committee.pk)
        data = StrongroomCommitteeSerializer(committee).data
        data['message'] = (
            'Committee submitted. The peer EC must approve before the nominee receives their custody key.'
        )
        return Response(data, status=status.HTTP_201_CREATED)


class ApproveCommitteeView(APIView):
    """Peer EC approves the custody committee; nominee then receives a timed hashed key."""
    permission_classes = [IsStrongroomAdmin]

    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        try:
            committee = approve_committee(election=election, actor=request.user)
        except CommitteeError as exc:
            return Response({'error': exc.message, 'code': exc.code}, status=exc.status)
        data = StrongroomCommitteeSerializer(committee).data
        data['message'] = (
            'Committee approved. A timed custody key was sent to the nominee.'
        )
        return Response(data)


class PublicVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        seal_hash = request.data.get('seal_hash')
        if not seal_hash:
            return Response({'error': 'seal_hash required'}, status=status.HTTP_400_BAD_REQUEST)

        election_seal = ElectionSeal.objects.filter(seal_hash=seal_hash).first()
        if election_seal:
            return Response({
                'type': 'election_seal',
                'valid': True,
                'election': election_seal.election.title,
                'created_at': election_seal.created_at,
                'status': election_seal.status,
            })

        ballot_seal = BallotSeal.objects.filter(seal_hash=seal_hash).first()
        if ballot_seal:
            return Response({
                'type': 'ballot_seal',
                'valid': True,
                'election': ballot_seal.election.title,
                'created_at': ballot_seal.created_at,
                'status': ballot_seal.status,
            })

        return Response({'valid': False, 'message': 'No matching seal found'})
