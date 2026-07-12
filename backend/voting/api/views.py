import hashlib
import random
import re
import string
from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from candidates.models import Candidate
from elections.models import Election, Position, VoterEligibility
from elections.services.scope_eligibility import student_can_access_election
from security.models import SVTToken
from system.settings_utils import get_setting_int
from voting.models import Vote

SVT_PATTERN = re.compile(r'^v-[a-z]{3}-\d{4}$')


def generate_svt():
    """Format: v-sda-4539 (prefix + 3 letters + 4 digits)."""
    letters = ''.join(random.choices(string.ascii_lowercase, k=3))
    digits = f'{random.randint(0, 9999):04d}'
    return f'v-{letters}-{digits}'


def normalize_svt(code):
    raw = (code or '').strip().lower().replace(' ', '')
    compact = raw.replace('-', '')
    if re.fullmatch(r'v[a-z]{3}\d{4}', compact):
        return f'v-{compact[1:4]}-{compact[4:]}'
    return raw


def hash_svt(code):
    return hashlib.sha256(normalize_svt(code).encode()).hexdigest()


def candidate_department_label(candidate):
    if candidate.academic_department_id and candidate.academic_department:
        return candidate.academic_department.name
    return candidate.department or ''


def candidate_photo_url(candidate, request=None):
    if not candidate.photo:
        return None
    # Relative /media path so Vite LAN proxy can serve photos on all devices
    return candidate.photo.url


def _active_issued_svt(user, election):
    now = timezone.now()
    return (
        SVTToken.objects.filter(
            user=user,
            election=election,
            status='issued',
            expires_at__gt=now,
        )
        .order_by('-issued_at')
        .first()
    )


def _active_validated_svt(user, election):
    now = timezone.now()
    svt = (
        SVTToken.objects.filter(
            user=user,
            election=election,
            status='validated',
        )
        .order_by('-validated_at', '-issued_at')
        .first()
    )
    if not svt:
        return None
    if svt.expires_at <= now:
        svt.status = 'expired'
        svt.save(update_fields=['status'])
        return None
    return svt


def _svt_session_payload(svt, status_name):
    now = timezone.now()
    expires_in = max(0, int((svt.expires_at - now).total_seconds())) if svt else 0
    return {
        'status': status_name,
        'svt_id': str(svt.svt_id) if svt else None,
        'expires_at': svt.expires_at.isoformat() if svt else None,
        'expires_in_seconds': expires_in,
    }


def _revoke_open_svts(user, election):
    """Expire any issued/validated tokens so older codes cannot be reused."""
    SVTToken.objects.filter(
        user=user,
        election=election,
        status__in=['issued', 'validated'],
    ).update(status='expired')


def _svt_request_count_last_hour(user, election):
    cutoff = timezone.now() - timedelta(hours=1)
    return SVTToken.objects.filter(
        user=user,
        election=election,
        issued_at__gte=cutoff,
    ).count()


class EligibleElectionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        eligibilities = VoterEligibility.objects.filter(
            user=user,
            is_eligible=True,
            election__status='open',
        ).select_related('election')

        elections_data = []
        for el in eligibilities:
            election = el.election
            if not student_can_access_election(user, election):
                continue
            elections_data.append({
                'uuid': election.uuid,
                'title': election.title,
                'description': election.description,
                'status': election.status,
                'start_date': election.start_date,
                'end_date': election.end_date,
                'voter_count': VoterEligibility.objects.filter(
                    election=election, is_eligible=True
                ).count(),
            })
        return Response(elections_data)


class SVTRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user
        force_resend = bool(request.data.get('resend') or request.data.get('force'))

        if election.status != 'open':
            return Response({'error': 'Election is not open'}, status=status.HTTP_400_BAD_REQUEST)

        if not student_can_access_election(user, election):
            return Response(
                {'error': 'You are not eligible for this election'},
                status=status.HTTP_403_FORBIDDEN,
            )

        max_per_hour = max(1, get_setting_int('svt_max_requests_per_hour', 5))
        if _svt_request_count_last_hour(user, election) >= max_per_hour:
            return Response(
                {'error': 'Too many SVT requests. Please wait and try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        active = _active_issued_svt(user, election)

        # First request / normal request: keep the unexpired token, do not mint another.
        if active and not force_resend:
            return Response({
                'message': 'An SVT was already issued and is still valid. Enter that token to continue.',
                'svt_id': active.svt_id,
                'already_issued': True,
                'expires_at': active.expires_at,
            })

        # Explicit resend: revoke previous tokens so the first code is no longer accepted.
        if force_resend:
            cooldown = max(0, get_setting_int('svt_resend_cooldown_seconds', 60))
            latest = (
                SVTToken.objects.filter(user=user, election=election)
                .order_by('-issued_at')
                .first()
            )
            if latest and latest.last_resent_at:
                elapsed = (timezone.now() - latest.last_resent_at).total_seconds()
                if elapsed < cooldown:
                    wait = int(cooldown - elapsed)
                    return Response(
                        {'error': f'Please wait {wait}s before requesting another SVT.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )
            elif latest and cooldown:
                elapsed = (timezone.now() - latest.issued_at).total_seconds()
                if elapsed < cooldown:
                    wait = int(cooldown - elapsed)
                    return Response(
                        {'error': f'Please wait {wait}s before requesting another SVT.'},
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )

            _revoke_open_svts(user, election)

        code = generate_svt()
        hashed = hash_svt(code)
        expiry_minutes = max(1, get_setting_int('svt_expiry_minutes', 10))
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        svt = SVTToken.objects.create(
            user=user,
            election=election,
            token_hash=hashed,
            status='issued',
            expires_at=expires_at,
            last_resent_at=timezone.now() if force_resend else None,
        )

        print(f'🔑 SVT for {user.email} (election: {election.title}): {code}')

        return Response({
            'message': 'SVT sent to your phone' if not force_resend else 'A new SVT was issued. Previous tokens are no longer valid.',
            'svt_id': svt.svt_id,
            'already_issued': False,
            'resent': force_resend,
        })


class SVTValidateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user
        svt_code = normalize_svt(request.data.get('svt_code'))

        if not svt_code:
            return Response({'error': 'SVT code required'}, status=status.HTTP_400_BAD_REQUEST)

        if not SVT_PATTERN.fullmatch(svt_code):
            return Response(
                {'error': 'Invalid Secure Voting Token. Check the code you received and try again.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Idempotent resume: already validated + still active + matching code
        active_validated = _active_validated_svt(user, election)
        if active_validated and hash_svt(svt_code) == active_validated.token_hash:
            return Response({
                'message': 'SVT already validated',
                'already_validated': True,
                **_svt_session_payload(active_validated, 'validated'),
            })

        svt = (
            SVTToken.objects.filter(user=user, election=election, status='issued')
            .order_by('-issued_at')
            .first()
        )

        if not svt:
            return Response(
                {'error': 'No valid SVT found. Request a new one.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now() > svt.expires_at:
            svt.status = 'expired'
            svt.save(update_fields=['status'])
            return Response(
                {'error': 'SVT expired. Request a new one.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_attempts = max(1, get_setting_int('svt_max_validation_attempts', 5))
        if svt.validation_attempts >= max_attempts:
            svt.status = 'revoked'
            svt.save(update_fields=['status'])
            return Response(
                {'error': 'Too many invalid attempts. Request a new SVT.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if hash_svt(svt_code) != svt.token_hash:
            svt.validation_attempts += 1
            updates = ['validation_attempts']
            if svt.validation_attempts >= max_attempts:
                svt.status = 'revoked'
                updates.append('status')
            svt.save(update_fields=updates)
            if svt.status == 'revoked':
                return Response(
                    {'error': 'Too many invalid attempts. Request a new SVT.'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )
            return Response({'error': 'Invalid SVT code'}, status=status.HTTP_400_BAD_REQUEST)

        svt.status = 'validated'
        svt.validated_at = timezone.now()
        svt.save(update_fields=['status', 'validated_at'])

        return Response({
            'message': 'SVT validated successfully',
            'already_validated': False,
            **_svt_session_payload(svt, 'validated'),
        })


class SVTSessionView(APIView):
    """Return whether the voter has an issued/validated SVT for this election."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user

        validated = _active_validated_svt(user, election)
        if validated:
            return Response(_svt_session_payload(validated, 'validated'))

        issued = _active_issued_svt(user, election)
        if issued:
            return Response(_svt_session_payload(issued, 'issued'))

        # Surface expired so the client can clear local session
        expired = (
            SVTToken.objects.filter(
                user=user,
                election=election,
                status__in=['expired', 'issued', 'validated'],
            )
            .order_by('-issued_at')
            .first()
        )
        if expired and expired.status == 'expired':
            return Response({'status': 'expired'})
        if expired and expired.expires_at <= timezone.now():
            if expired.status in ('issued', 'validated'):
                expired.status = 'expired'
                expired.save(update_fields=['status'])
            return Response({'status': 'expired'})

        return Response({'status': 'none'})


class BallotView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user

        if election.status != 'open':
            return Response({'error': 'Election is not open'}, status=status.HTTP_400_BAD_REQUEST)

        svt = _active_validated_svt(user, election)
        if not svt:
            return Response({'error': 'Valid SVT required'}, status=status.HTTP_400_BAD_REQUEST)

        positions = (
            Position.objects.filter(
                election=election,
                is_active=True,
                is_votable=True,
            )
            .order_by('display_order')
            .prefetch_related('candidates__academic_department')
        )

        ballot_data = []
        for pos in positions:
            candidates = pos.candidates.filter(status='approved').order_by('ballot_number')
            ballot_data.append({
                'uuid': pos.uuid,
                'title': pos.title,
                'description': pos.description,
                'max_votes_allowed': pos.max_votes_allowed,
                'candidates': [
                    {
                        'uuid': str(c.uuid),
                        'full_name': c.full_name,
                        'department': candidate_department_label(c),
                        'ballot_number': c.ballot_number,
                        'photo': candidate_photo_url(c, request),
                    }
                    for c in candidates
                ],
            })

        return Response({
            'positions': ballot_data,
            'election_title': election.title,
            'svt_expires_at': svt.expires_at.isoformat(),
            'svt_expires_in_seconds': max(0, int((svt.expires_at - timezone.now()).total_seconds())),
        })


class SubmitVoteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user
        svt_code = normalize_svt(request.data.get('svt_code'))
        selections = request.data.get('selections', [])

        svt = _active_validated_svt(user, election)
        if not svt:
            return Response(
                {'error': 'Your secure token expired. Request a new one to continue.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If a code is provided, it must match; otherwise the validated session is enough
        if svt_code and hash_svt(svt_code) != svt.token_hash:
            return Response({'error': 'Invalid SVT code'}, status=status.HTTP_400_BAD_REQUEST)

        if election.status != 'open':
            return Response({'error': 'Election is not open'}, status=status.HTTP_400_BAD_REQUEST)

        votes_created = []
        for sel in selections:
            position_uuid = sel.get('position_uuid')
            candidate_uuids = sel.get('candidate_uuids', [])

            position = get_object_or_404(Position, uuid=position_uuid, election=election)
            if not position.is_votable:
                return Response(
                    {'error': f'Position {position.title} is not votable'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if len(candidate_uuids) > position.max_votes_allowed:
                return Response(
                    {'error': f'Too many candidates selected for {position.title}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for candidate_uuid in candidate_uuids:
                candidate = get_object_or_404(
                    Candidate, uuid=candidate_uuid, position=position, status='approved'
                )
                if Vote.objects.filter(user=user, position=position, candidate=candidate).exists():
                    return Response(
                        {'error': f'You already voted for {candidate.full_name}'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                vote_hash = hashlib.sha256(
                    f'{user.uuid}{election.uuid}{position.uuid}{candidate.uuid}{timezone.now().isoformat()}'.encode()
                ).hexdigest()
                from elections.models import VotingChannel

                web_channel = VotingChannel.objects.get(channel_name='web')
                vote = Vote.objects.create(
                    user=user,
                    election=election,
                    position=position,
                    candidate=candidate,
                    channel=web_channel,
                    svt=svt,
                    vote_hash=vote_hash,
                )
                votes_created.append(vote)

        svt.status = 'used'
        svt.used_at = timezone.now()
        svt.save(update_fields=['status', 'used_at'])

        confirmation_code = f'VTB-{str(election.uuid)[:4]}-{random.randint(100000, 999999)}'

        return Response({
            'message': 'Vote submitted successfully',
            'confirmation_code': confirmation_code,
            'votes': len(votes_created),
        })
