import hashlib
import random
import re
import string
from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from candidates.models import Candidate
from elections.models import Election, Position
from elections.services.register_service import election_register_user_count
from elections.services.scope_eligibility import student_can_access_election
from accounts.models import User
from accounts.permissions import IsMainEC
from security.models import SVTAbuseBlock, SVTToken
from system.settings_utils import get_setting_int
from voting.models import Vote, PreVotePresenceCapture
from notifications.sms import mask_phone
from notifications.tasks import dispatch_svt_sms

SVT_PATTERN = re.compile(r'^v-[a-z]{3}-\d{4}$')

ALREADY_VOTED_MSG = 'You have already cast your vote for this election.'


def user_has_voted(user, election):
    return Vote.objects.filter(user=user, election=election).exists()


def already_voted_response():
    return Response(
        {'error': ALREADY_VOTED_MSG, 'has_voted': True},
        status=status.HTTP_400_BAD_REQUEST,
    )


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


def candidate_photo_url(candidate, request=None):
    if not candidate.photo:
        return None
    # Relative /media path so Vite LAN proxy can serve photos on all devices
    return candidate.photo.url


def _svt_issue_expires_at():
    """Issued SVTs are live for a short window (default 20 minutes)."""
    minutes = get_setting_int('svt_expiry_minutes', 20)
    if minutes <= 0:
        minutes = 20
    return timezone.now() + timedelta(minutes=minutes)


def _svt_validated_expires_at(election):
    """
    After successful validation, keep the voter authenticated through the
    rest of voting (network blips included) until they cast a ballot or
    the election closes.
    """
    now = timezone.now()
    if election.end_date and election.end_date > now:
        return election.end_date
    return now + timedelta(hours=12)


def _resolve_voter_phone(user, election, preferred_msisdn: str | None = None):
    """
    Prefer account phone; fall back to register entry phone for this election.
    If preferred_msisdn (e.g. dialing USSD number) matches a stored phone, use that.
    """
    from django.db.models import Q
    from elections.models import VoterRegisterEntry
    from ussd.services.ussd_auth import msisdn_matches_phone

    candidates = []
    phone = (getattr(user, 'phone_number', None) or '').strip()
    if phone:
        candidates.append(phone)

    scope = (
        Q(register=election.register)
        if getattr(election, 'register_id', None)
        else Q(register__election=election)
    )
    entries = (
        VoterRegisterEntry.objects
        .filter(user=user)
        .filter(scope)
        .exclude(phone_number__isnull=True)
        .exclude(phone_number='')
        .order_by('-created_at')[:5]
    )
    for entry in entries:
        value = (entry.phone_number or '').strip()
        if value and value not in candidates:
            candidates.append(value)

    if preferred_msisdn:
        for candidate in candidates:
            if msisdn_matches_phone(preferred_msisdn, candidate):
                return candidate

    return candidates[0] if candidates else ''


def _active_issued_svt(user, election):
    now = timezone.now()
    if election.status != 'open':
        return None
    svt = (
        SVTToken.objects.filter(
            user=user,
            election=election,
            status='issued',
        )
        .order_by('-issued_at')
        .first()
    )
    if not svt:
        return None
    if svt.expires_at <= now:
        svt.status = 'expired'
        svt.save(update_fields=['status'])
        return None
    return svt


def _active_validated_svt(user, election):
    """Validated SVTs remain usable until vote cast or election closes."""
    now = timezone.now()
    if election.status != 'open':
        return None
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


def _has_presence_capture(user, election, svt):
    """True when this voter has an audit selfie for the active validated SVT."""
    if not svt:
        return False
    capture = (
        PreVotePresenceCapture.objects
        .filter(user=user, election=election, svt=svt)
        .order_by('-captured_at')
        .first()
    )
    if capture and capture.image and getattr(capture.image, 'name', ''):
        return True
    # Heal edge case: photo saved under a prior validated token for same election
    legacy = (
        PreVotePresenceCapture.objects
        .filter(user=user, election=election)
        .exclude(image='')
        .order_by('-captured_at')
        .first()
    )
    if legacy and legacy.image and getattr(legacy.image, 'name', ''):
        if legacy.svt_id != svt.svt_id:
            legacy.svt = svt
            legacy.save(update_fields=['svt'])
        return True
    return False


def _svt_session_payload(svt, status_name, user=None, election=None):
    now = timezone.now()
    expires_in = max(0, int((svt.expires_at - now).total_seconds())) if svt else 0
    payload = {
        'status': status_name,
        'svt_id': str(svt.svt_id) if svt else None,
        'expires_at': svt.expires_at.isoformat() if svt else None,
        'expires_in_seconds': expires_in,
    }
    if status_name == 'validated' and svt and user is not None and election is not None:
        payload['presence_captured'] = _has_presence_capture(user, election, svt)
    return payload


def presence_required_response():
    return Response(
        {
            'error': 'A presence photo is required before you can open the ballot.',
            'presence_required': True,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _revoke_open_svts(user, election):
    """Expire any issued/validated tokens so older codes cannot be reused."""
    now = timezone.now()
    SVTToken.objects.filter(
        user=user,
        election=election,
        status__in=['issued', 'validated'],
    ).update(status='expired', expires_at=now)


def _svt_request_count_total(user, election):
    """Lifetime request count for this voter on this election (one voter → capped SVTs)."""
    return SVTToken.objects.filter(user=user, election=election).count()


def _svt_max_requests():
    total = get_setting_int('svt_max_requests_total', 0)
    if total and total > 0:
        return max(1, total)
    return max(1, get_setting_int('svt_max_requests_per_hour', 3))


def _svt_resend_wait_seconds(user, election, cooldown):
    """Seconds remaining before another resend is allowed (0 = ok)."""
    if cooldown <= 0:
        return 0
    latest = (
        SVTToken.objects.filter(user=user, election=election)
        .order_by('-issued_at')
        .first()
    )
    if not latest:
        return 0
    anchor = latest.last_resent_at or latest.issued_at
    if not anchor:
        return 0
    elapsed = (timezone.now() - anchor).total_seconds()
    if elapsed >= cooldown:
        return 0
    return max(1, int(cooldown - elapsed))


def _active_abuse_block(user, election):
    now = timezone.now()
    block = (
        SVTAbuseBlock.objects
        .filter(user=user, election=election, blocked_until__gt=now)
        .order_by('-blocked_until')
        .first()
    )
    return block


def _block_user_for_foreign_svt(user, election, foreign_svt):
    minutes = max(1, get_setting_int('svt_cross_user_block_minutes', 60))
    until = timezone.now() + timedelta(minutes=minutes)
    return SVTAbuseBlock.objects.create(
        user=user,
        election=election,
        reason='foreign_svt_attempt',
        blocked_until=until,
        metadata={
            'foreign_svt_id': str(foreign_svt.svt_id),
            'foreign_user_id': str(foreign_svt.user_id),
        },
    )


def _abuse_block_response(block):
    remaining = max(0, int((block.blocked_until - timezone.now()).total_seconds()))
    minutes = max(1, (remaining + 59) // 60)
    return Response(
        {
            'error': (
                f'You attempted to use another voter’s Secure Voting Token. '
                f'Access is blocked for {minutes} minute(s).'
            ),
            'blocked': True,
            'blocked_until': block.blocked_until.isoformat(),
            'retry_after': remaining,
        },
        status=status.HTTP_403_FORBIDDEN,
    )


class EligibleElectionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        elections = Election.objects.filter(status='open').select_related('register')
        election_ids = [e.pk for e in elections]
        voted_at_map = {}
        if election_ids:
            for vote in (
                Vote.objects.filter(user=user, election_id__in=election_ids)
                .order_by('timestamp')
                .only('election_id', 'timestamp')
            ):
                voted_at_map.setdefault(vote.election_id, vote.timestamp)

        elections_data = []
        for election in elections:
            if not student_can_access_election(user, election):
                continue
            has_voted = election.pk in voted_at_map
            elections_data.append({
                'uuid': election.uuid,
                'title': election.title,
                'description': election.description,
                'status': election.status,
                'start_date': election.start_date,
                'end_date': election.end_date,
                'voter_count': election_register_user_count(election),
                'has_voted': has_voted,
                'voted_at': voted_at_map.get(election.pk),
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

        block = _active_abuse_block(user, election)
        if block:
            return _abuse_block_response(block)

        if not student_can_access_election(user, election):
            return Response(
                {'error': 'You are not eligible for this election'},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user_has_voted(user, election):
            return already_voted_response()

        # Already validated — stay authenticated; do not mint another SVT.
        validated = _active_validated_svt(user, election)
        if validated:
            return Response({
                'message': 'Your SVT is already validated. Continue voting.',
                'already_validated': True,
                **_svt_session_payload(validated, 'validated', user=user, election=election),
            })

        # Resend cooldown first
        if force_resend:
            cooldown = max(0, get_setting_int('svt_resend_cooldown_seconds', 60))
            wait = _svt_resend_wait_seconds(user, election, cooldown)
            if wait:
                return Response(
                    {
                        'error': f'Please wait {wait}s before requesting another token.',
                        'retry_after': wait,
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        max_requests = _svt_max_requests()
        used_requests = _svt_request_count_total(user, election)
        active = _active_issued_svt(user, election)

        # First request / normal request: keep the unexpired token (one voter → one live SVT).
        if active and not force_resend:
            phone = _resolve_voter_phone(user, election)
            return Response({
                'message': 'An SVT was already issued and is still valid. Enter that token to continue.',
                'svt_id': active.svt_id,
                'already_issued': True,
                'expires_at': active.expires_at,
                'expires_in_seconds': max(0, int((active.expires_at - timezone.now()).total_seconds())),
                'requests_remaining': max(0, max_requests - used_requests),
                'phone_masked': mask_phone(phone) if phone else None,
            })

        if used_requests >= max_requests:
            return Response(
                {
                    'error': (
                        f'You have reached the maximum of {max_requests} SVT requests '
                        'for this election.'
                    ),
                    'requests_remaining': 0,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        phone = _resolve_voter_phone(user, election)
        if not phone:
            return Response(
                {
                    'error': (
                        'No phone number is linked to your voter record. '
                        'Contact the Electoral Commission to update your details.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Explicit resend (or no active token): revoke previous open tokens.
        _revoke_open_svts(user, election)

        code = generate_svt()
        hashed = hash_svt(code)
        expires_at = _svt_issue_expires_at()
        svt = SVTToken.objects.create(
            user=user,
            election=election,
            token_hash=hashed,
            status='issued',
            expires_at=expires_at,
            last_resent_at=timezone.now() if force_resend else None,
        )

        sms_result = dispatch_svt_sms(
            phone=phone,
            code=code,
            election_title=election.title,
            election_uuid=str(election.uuid),
            user_uuid=str(user.uuid),
            wait=False,
        )
        if not sms_result.get('ok') and not sms_result.get('queued'):
            # Keep token issued so a retry can still validate if SMS eventually lands,
            # but surface the delivery issue clearly.
            return Response(
                {
                    'error': sms_result.get('error') or 'Could not deliver SVT SMS. Try again shortly.',
                    'svt_id': svt.svt_id,
                    'phone_masked': sms_result.get('masked_phone') or mask_phone(phone),
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            from notifications.services import notify_svt_issued, notify_svt_requested
            notify_svt_issued(
                user,
                election,
                expires_at=expires_at,
                phone_masked=sms_result.get('masked_phone') or mask_phone(phone),
            )
            notify_svt_requested(user, election)
        except Exception:
            pass

        return Response({
            'message': (
                f'SVT is being sent to {sms_result.get("masked_phone") or mask_phone(phone)}. '
                f'Valid for {max(1, int((expires_at - timezone.now()).total_seconds() // 60))} minutes. One use only.'
                if not force_resend
                else (
                    f'A new SVT is being sent to {sms_result.get("masked_phone") or mask_phone(phone)}. '
                    'Previous tokens are no longer valid.'
                )
            ),
            'svt_id': svt.svt_id,
            'already_issued': False,
            'resent': force_resend,
            'sms_queued': bool(sms_result.get('queued')),
            'expires_at': expires_at,
            'expires_in_seconds': max(0, int((expires_at - timezone.now()).total_seconds())),
            'requests_remaining': max(0, max_requests - (used_requests + 1)),
            'phone_masked': sms_result.get('masked_phone') or mask_phone(phone),
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

        block = _active_abuse_block(user, election)
        if block:
            return _abuse_block_response(block)

        if user_has_voted(user, election):
            return already_voted_response()

        token_hash = hash_svt(svt_code)

        # Idempotent resume: already validated + still active + matching code
        active_validated = _active_validated_svt(user, election)
        if active_validated and token_hash == active_validated.token_hash:
            return Response({
                'message': 'SVT already validated',
                'already_validated': True,
                **_svt_session_payload(active_validated, 'validated', user=user, election=election),
            })

        # Cross-user attempt: live token belonging to someone else → block this user 1 hour
        foreign = (
            SVTToken.objects
            .filter(election=election, token_hash=token_hash)
            .exclude(user=user)
            .filter(status__in=['issued', 'validated'])
            .order_by('-issued_at')
            .first()
        )
        if foreign:
            if foreign.expires_at <= timezone.now():
                foreign.status = 'expired'
                foreign.save(update_fields=['status'])
            else:
                new_block = _block_user_for_foreign_svt(user, election, foreign)
                return _abuse_block_response(new_block)

        svt = (
            SVTToken.objects.filter(user=user, election=election, status='issued')
            .order_by('-issued_at')
            .first()
        )

        if not svt:
            # Used / expired token with matching hash → explicit messaging
            prior = (
                SVTToken.objects
                .filter(user=user, election=election, token_hash=token_hash)
                .order_by('-issued_at')
                .first()
            )
            if prior and prior.status == 'used':
                return Response(
                    {'error': 'This SVT has already been used and cannot be reused.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if prior and prior.status in ('expired', 'revoked'):
                return Response(
                    {'error': 'This SVT has expired. Request a new one if you still have requests left.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
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

        if token_hash != svt.token_hash:
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

        # Bind authentication for the rest of voting (network resume safe).
        svt.status = 'validated'
        svt.validated_at = timezone.now()
        svt.expires_at = _svt_validated_expires_at(election)
        svt.save(update_fields=['status', 'validated_at', 'expires_at'])

        return Response({
            'message': 'SVT validated successfully',
            'already_validated': False,
            **_svt_session_payload(svt, 'validated', user=user, election=election),
        })


class SVTSessionView(APIView):
    """Return whether the voter has an issued/validated SVT for this election."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user

        if user_has_voted(user, election):
            return Response({'status': 'voted', 'has_voted': True})

        validated = _active_validated_svt(user, election)
        if validated:
            return Response(_svt_session_payload(validated, 'validated', user=user, election=election))

        issued = _active_issued_svt(user, election)
        if issued:
            return Response(_svt_session_payload(issued, 'issued', user=user, election=election))

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


class PresenceCaptureView(APIView):
    """Audit presence selfie required after SVT validation, before the ballot."""

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user

        if user_has_voted(user, election):
            return already_voted_response()

        svt = _active_validated_svt(user, election)
        if not svt:
            return Response({'error': 'Valid SVT required'}, status=status.HTTP_400_BAD_REQUEST)

        has_image = _has_presence_capture(user, election, svt)
        capture = None
        if has_image:
            capture = (
                PreVotePresenceCapture.objects.filter(user=user, election=election, svt=svt)
                .order_by('-captured_at')
                .first()
            )
            if not (capture and capture.image):
                capture = (
                    PreVotePresenceCapture.objects.filter(user=user, election=election)
                    .exclude(image='')
                    .order_by('-captured_at')
                    .first()
                )
        return Response({
            'presence_captured': has_image,
            'captured_at': capture.captured_at.isoformat() if capture else None,
            'image_url': request.build_absolute_uri(capture.image.url) if capture and capture.image else None,
        })

    @transaction.atomic
    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user

        if election.status != 'open':
            return Response({'error': 'Election is not open'}, status=status.HTTP_400_BAD_REQUEST)

        if user_has_voted(user, election):
            return already_voted_response()

        svt = _active_validated_svt(user, election)
        if not svt:
            return Response(
                {'error': 'Validate your Secure Voting Token before capturing a photo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image = request.FILES.get('image') or request.FILES.get('photo')
        if not image:
            return Response({'error': 'Photo is required'}, status=status.HTTP_400_BAD_REQUEST)

        content_type = (getattr(image, 'content_type', '') or '').lower()
        name = (getattr(image, 'name', '') or '').lower()
        allowed_types = ('image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'application/octet-stream')
        looks_like_image = name.endswith(('.jpg', '.jpeg', '.png', '.webp'))
        if content_type and content_type not in allowed_types and not looks_like_image:
            return Response(
                {'error': 'Use a JPEG, PNG, or WebP photo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ~6MB soft cap for mobile camera shots
        if getattr(image, 'size', 0) and image.size > 6 * 1024 * 1024:
            return Response(
                {'error': 'Photo is too large. Please retake a clearer, smaller shot.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        capture, _created = PreVotePresenceCapture.objects.get_or_create(
            user=user,
            election=election,
            svt=svt,
            defaults={'channel': 'web'},
        )
        if capture.image:
            capture.image.delete(save=False)
        capture.image = image
        capture.channel = 'web'
        capture.save()

        return Response({
            'message': 'Presence photo saved for audit.',
            'presence_captured': True,
            'captured_at': capture.captured_at.isoformat(),
            'uuid': str(capture.uuid),
        }, status=status.HTTP_201_CREATED)


class BallotView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user

        block = _active_abuse_block(user, election)
        if block:
            return _abuse_block_response(block)

        if election.status != 'open':
            return Response({'error': 'Election is not open'}, status=status.HTTP_400_BAD_REQUEST)

        if user_has_voted(user, election):
            return already_voted_response()

        svt = _active_validated_svt(user, election)
        if not svt:
            return Response({'error': 'Valid SVT required'}, status=status.HTTP_400_BAD_REQUEST)

        if not _has_presence_capture(user, election, svt):
            return presence_required_response()

        positions = (
            Position.objects.filter(
                election=election,
                is_active=True,
                is_votable=True,
            )
            .order_by('display_order')
            .prefetch_related('candidates', 'restricted_categories')
        )

        ballot_data = []
        for pos in positions:
            if not pos.voter_may_see(user):
                continue
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
                        'ballot_number': c.ballot_number,
                        'photo': candidate_photo_url(c, request),
                    }
                    for c in candidates
                ],
            })

        from system.models import InstitutionProfile

        profile = InstitutionProfile.objects.first()
        election_year = ''
        if election.start_date:
            election_year = str(election.start_date.year)
        elif election.end_date:
            election_year = str(election.end_date.year)

        branding = {
            'institution_name': '',
            'institution_short_name': '',
            'logo': None,
            'election_year': election_year,
            'election_type': '',
        }
        if profile:
            name = (profile.name or '').strip()
            short = (profile.short_name or '').strip()
            blocked = {'voterb', 'votebridge'}
            branding['institution_name'] = '' if name.lower() in blocked else name
            branding['institution_short_name'] = '' if short.lower() in blocked else short
            branding['logo'] = profile.logo.url if profile.logo else None

        return Response({
            'positions': ballot_data,
            'election_title': election.title,
            'branding': branding,
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

        block = _active_abuse_block(user, election)
        if block:
            return _abuse_block_response(block)

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

        if user_has_voted(user, election):
            return already_voted_response()

        if not _has_presence_capture(user, election, svt):
            return presence_required_response()

        votes_created = []
        for sel in selections:
            position_uuid = sel.get('position_uuid')
            candidate_uuids = [c for c in (sel.get('candidate_uuids') or []) if c]
            # Skipped races must not create ballot entries.
            if not candidate_uuids:
                continue

            position = get_object_or_404(Position, uuid=position_uuid, election=election)
            if not position.is_votable:
                return Response(
                    {'error': f'Position {position.title} is not votable'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not position.is_active:
                return Response(
                    {'error': f'Position {position.title} is not active'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not position.voter_may_see(user):
                return Response(
                    {'error': f'You are not eligible to vote for {position.title}'},
                    status=status.HTTP_403_FORBIDDEN,
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

                web_channel, _ = VotingChannel.objects.get_or_create(
                    channel_name='web',
                    defaults={'is_active': True},
                )
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

        if not votes_created:
            return Response(
                {'error': 'Select at least one candidate before submitting your ballot.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        svt.status = 'used'
        svt.used_at = timezone.now()
        svt.expires_at = timezone.now()
        svt.save(update_fields=['status', 'used_at', 'expires_at'])

        confirmation_code = f'VTB-{str(election.uuid)[:4]}-{random.randint(100000, 999999)}'

        presence = (
            PreVotePresenceCapture.objects.filter(user=user, election=election, svt=svt)
            .exclude(image='')
            .order_by('-captured_at')
            .first()
        )
        if not presence:
            presence = (
                PreVotePresenceCapture.objects.filter(user=user, election=election)
                .exclude(image='')
                .order_by('-captured_at')
                .first()
            )

        from security.services.vote_audit import record_vote_cast_audit
        from strongroom.services import seal_vote_cast
        from elections.ws import broadcast_election_monitor

        positions_count = len({
            str(vote.position_id)
            for vote in votes_created
        })
        audit_log = record_vote_cast_audit(
            request=request,
            user=user,
            election=election,
            confirmation_code=confirmation_code,
            positions_count=positions_count,
            presence_capture=presence,
            client_context=request.data.get('client_context') or request.data.get('device_context'),
        )
        seal_vote_cast(
            election=election,
            confirmation_code=confirmation_code,
            audit_log=audit_log,
            presence_capture=presence,
            svt=svt,
            channel='web',
        )
        try:
            broadcast_election_monitor(election)
        except Exception:
            pass

        return Response({
            'message': 'Vote submitted successfully',
            'confirmation_code': confirmation_code,
            'votes': len(votes_created),
        })


class ClearStudentVoteView(APIView):
    """Testing helper: wipe a student's votes + SVTs so they can revote."""

    permission_classes = [IsMainEC]

    @transaction.atomic
    def post(self, request, uuid, user_uuid):
        election = get_object_or_404(Election, uuid=uuid)
        student = get_object_or_404(User, uuid=user_uuid)

        votes_qs = Vote.objects.filter(election=election, user=student)
        vote_count = votes_qs.count()
        # Votes / presence PROTECT SVT — delete dependents first
        votes_qs.delete()
        PreVotePresenceCapture.objects.filter(election=election, user=student).delete()

        svt_qs = SVTToken.objects.filter(election=election, user=student)
        svt_count = svt_qs.count()
        svt_qs.delete()

        return Response({
            'message': 'Student voting data cleared; they can request a new SVT and revote.',
            'votes_deleted': vote_count,
            'svt_tokens_deleted': svt_count,
            'user_uuid': str(student.uuid),
            'election_uuid': str(election.uuid),
        })
