import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from strongroom.models import (
    StrongroomAccessSession,
    CustodyRecord,
    VaultAccessRequest,
    VaultSession,
    VaultEvidence,
)


VAULT_SESSION_TTL_MINUTES = 30


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_vault_session(user, request=None):
    """Create a step-up vault gate session after password verification."""
    StrongroomAccessSession.objects.filter(
        user=user, is_active=True
    ).update(is_active=False, closed_at=timezone.now())

    token = secrets.token_urlsafe(48)
    expires_at = timezone.now() + timedelta(minutes=VAULT_SESSION_TTL_MINUTES)

    session = StrongroomAccessSession.objects.create(
        user=user,
        token_hash=_hash_token(token),
        expires_at=expires_at,
        ip_address=_client_ip(request),
        user_agent=_user_agent(request),
    )

    CustodyRecord.objects.create(
        election=None,
        action='vault_entered',
        actor=user,
        metadata={
            'session_uuid': str(session.uuid),
            'ip_address': session.ip_address,
        },
    )

    return token, session


def get_active_session(user, vault_token):
    if not vault_token or not user:
        return None

    session = StrongroomAccessSession.objects.filter(
        user=user,
        token_hash=_hash_token(vault_token),
        is_active=True,
    ).first()

    if not session:
        return None
    if session.expires_at <= timezone.now():
        close_vault_session(session, user, reason='expired')
        return None
    return session


def close_vault_session(session, user, reason='manual'):
    session.is_active = False
    session.closed_at = timezone.now()
    session.save(update_fields=['is_active', 'closed_at'])

    CustodyRecord.objects.create(
        election=None,
        action='vault_exited',
        actor=user,
        metadata={
            'session_uuid': str(session.uuid),
            'reason': reason,
        },
    )


def request_election_access(election, user, reason):
    """Grant vault access to a specific election custody record."""
    access_request, _ = VaultAccessRequest.objects.get_or_create(
        election=election,
        requested_by=user,
        defaults={'reason': reason, 'status': 'approved'},
    )
    if access_request.status != 'approved':
        access_request.status = 'approved'
        access_request.reason = reason
        access_request.reviewed_by = user
        access_request.reviewed_at = timezone.now()
        access_request.save()

    vault_session, _ = VaultSession.objects.get_or_create(
        access_request=access_request,
        opened_by=user,
        defaults={'status': 'active'},
    )
    if vault_session.status != 'active':
        vault_session.status = 'active'
        vault_session.save()

    CustodyRecord.objects.create(
        election=election,
        action='vault_access_granted',
        actor=user,
        metadata={'reason': reason, 'request_uuid': str(access_request.uuid)},
    )

    return access_request, vault_session


def log_seal_reveal(election, user, seal_type, seal_uuid, seal_hash):
    access_request = VaultAccessRequest.objects.filter(
        election=election, requested_by=user, status='approved'
    ).first()
    if not access_request:
        access_request = VaultAccessRequest.objects.create(
            election=election,
            requested_by=user,
            reason='Seal inspection',
            status='approved',
            reviewed_by=user,
            reviewed_at=timezone.now(),
        )

    vault_session = VaultSession.objects.filter(
        access_request=access_request, opened_by=user, status='active'
    ).first()
    if not vault_session:
        vault_session = VaultSession.objects.create(
            access_request=access_request,
            opened_by=user,
            status='active',
        )

    VaultEvidence.objects.create(
        session=vault_session,
        seal_type=seal_type,
        seal_hash=seal_hash,
        seal_uuid=seal_uuid,
        viewed_by=user,
    )

    CustodyRecord.objects.create(
        election=election,
        action='seal_revealed',
        actor=user,
        metadata={
            'seal_type': seal_type,
            'seal_uuid': str(seal_uuid),
            'seal_hash_prefix': seal_hash[:16],
        },
    )


def _client_ip(request):
    if not request:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _user_agent(request):
    if not request:
        return ''
    return (request.META.get('HTTP_USER_AGENT') or '')[:255]
