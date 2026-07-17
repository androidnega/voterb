from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.permissions import IsStrongroomViewer, IsAdmin
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
from strongroom.services import (
    create_vault_session,
    get_active_session,
    close_vault_session,
    request_election_access,
    log_seal_reveal,
    VAULT_SESSION_TTL_MINUTES,
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
        elections = Election.objects.all().order_by('-created_at')
        return Response({
            'has_approved_committee': has_any_approved_committee(),
            'elections': CommitteeOverviewSerializer(elections, many=True).data,
        })


class VaultAuthenticateView(APIView):
    """Step-up password verification to open the strongroom vault."""
    permission_classes = [IsStrongroomViewer]

    def post(self, request):
        if not has_any_approved_committee():
            return _committee_required_response(
                'Vault opens after a custody committee is approved for at least one election'
            )

        password = request.data.get('password', '')
        if not password:
            return Response({'error': 'Password required for vault access'}, status=status.HTTP_400_BAD_REQUEST)

        if not request.user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_403_FORBIDDEN)

        token, session = create_vault_session(request.user, request)
        return Response({
            'vault_token': token,
            'session_uuid': str(session.uuid),
            'expires_at': session.expires_at.isoformat(),
            'ttl_minutes': VAULT_SESSION_TTL_MINUTES,
            'message': 'Vault access granted',
        })


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
    """Admin (EC) nominates a strongroom committee for an election."""
    permission_classes = [IsAdmin]

    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        members = request.data.get('members') or []
        if not isinstance(members, list) or len(members) == 0:
            return Response(
                {'error': 'Provide members: [{user_uuid, role}, ...]'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        committee, _ = StrongroomCommittee.objects.get_or_create(
            election=election,
            defaults={'nominated_by': request.user, 'status': 'submitted'},
        )
        committee.nominated_by = request.user
        committee.status = 'submitted'
        committee.save(update_fields=['nominated_by', 'status', 'updated_at'])

        for item in members:
            user_uuid = item.get('user_uuid')
            role = item.get('role') or 'custodian'
            if not user_uuid:
                continue
            member_user = get_object_or_404(User, uuid=user_uuid)
            StrongroomCommitteeMember.objects.update_or_create(
                committee=committee,
                user=member_user,
                defaults={'role': role},
            )

        CustodyRecord.objects.create(
            election=election,
            action='committee_nominated',
            actor=request.user,
            metadata={'committee_uuid': str(committee.uuid), 'member_count': len(members)},
        )
        committee = StrongroomCommittee.objects.prefetch_related('members__user').get(pk=committee.pk)
        return Response(StrongroomCommitteeSerializer(committee).data, status=status.HTTP_201_CREATED)


class ApproveCommitteeView(APIView):
    """Main EC approves a nominated custody committee."""
    permission_classes = [IsAdmin]

    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        committee = StrongroomCommittee.objects.filter(election=election).order_by('-updated_at').first()
        if not committee:
            return Response({'error': 'No committee nomination found'}, status=status.HTTP_404_NOT_FOUND)
        if committee.status not in ['submitted', 'draft']:
            return Response(
                {'error': f'Committee cannot be approved from status={committee.status}'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        committee.status = 'approved'
        committee.save(update_fields=['status', 'updated_at'])
        CustodyRecord.objects.create(
            election=election,
            action='committee_approved',
            actor=request.user,
            metadata={'committee_uuid': str(committee.uuid)},
        )
        return Response(StrongroomCommitteeSerializer(committee).data)


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
