"""Custody committee nomination, approval, nominee key, and 3-party vault unlock."""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password

from accounts.models import User
from accounts.org import user_is_main_ec, user_is_sub_ec
from strongroom.models import (
    CustodyRecord,
    StrongroomCommittee,
    StrongroomCommitteeMember,
    VaultUnlockChallenge,
)
from strongroom.services import create_vault_session, VAULT_SESSION_TTL_MINUTES


NOMINEE_KEY_TTL_MINUTES = 30
UNLOCK_CHALLENGE_TTL_MINUTES = 20


class CommitteeError(Exception):
    def __init__(self, message, code='committee_error', status=400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


def _hash_key(raw: str) -> str:
    return hashlib.sha256((raw or '').strip().lower().encode()).hexdigest()


def generate_nominee_key() -> str:
    """Compact hashed-looking digits+letters code for SMS (e.g. 7K2M-9Q4P)."""
    alphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    left = ''.join(secrets.choice(alphabet) for _ in range(4))
    right = ''.join(secrets.choice(alphabet) for _ in range(4))
    return f'{left}-{right}'


def issue_nominee_key(committee: StrongroomCommittee) -> str:
    raw = generate_nominee_key()
    committee.nominee_key_hash = make_password(_hash_key(raw))
    committee.nominee_key_expires_at = timezone.now() + timedelta(minutes=NOMINEE_KEY_TTL_MINUTES)
    committee.nominee_key_sent_at = timezone.now()
    committee.save(update_fields=[
        'nominee_key_hash', 'nominee_key_expires_at', 'nominee_key_sent_at', 'updated_at',
    ])
    _deliver_nominee_key(committee, raw)
    return raw


def _deliver_nominee_key(committee: StrongroomCommittee, raw_key: str):
    phone = (committee.nominee_phone or '').strip()
    if not phone:
        return
    message = (
        f'VoteBridge custody key for "{committee.election.title}": {raw_key}. '
        f'Valid {NOMINEE_KEY_TTL_MINUTES} minutes. Do not share.'
    )
    try:
        from notifications.sms import send_sms
        send_sms(phone=phone, message=message)
    except Exception:
        # DEBUG consoles still print keys via SMS layer when configured.
        print(f'[custody-key] {committee.nominee_full_name} {phone}: {raw_key}')


def verify_nominee_key(committee: StrongroomCommittee, raw_key: str) -> bool:
    if not committee.nominee_key_hash:
        return False
    if committee.nominee_key_expires_at and committee.nominee_key_expires_at <= timezone.now():
        return False
    return check_password(_hash_key(raw_key), committee.nominee_key_hash)


def nominate_committee(
    *,
    election,
    actor: User,
    peer_ec_uuid,
    nominee_full_name: str,
    nominee_phone: str,
    nominee_email: str = '',
) -> StrongroomCommittee:
    if not (user_is_main_ec(actor) or user_is_sub_ec(actor)):
        raise CommitteeError('Only Main EC or Sub EC can nominate a custody committee.', code='forbidden', status=403)

    peer = User.objects.filter(uuid=peer_ec_uuid).first()
    if not peer:
        raise CommitteeError('Peer EC not found.')
    if peer.pk == actor.pk:
        raise CommitteeError('Peer EC must be a different institutional EC member.')
    if not (user_is_main_ec(peer) or user_is_sub_ec(peer)):
        raise CommitteeError('Peer must be an Electoral Commission member.')

    name = (nominee_full_name or '').strip()
    phone = (nominee_phone or '').strip()
    email = (nominee_email or '').strip()
    if not name or not phone:
        raise CommitteeError('Nominee full name and phone are required.')

    with transaction.atomic():
        committee = StrongroomCommittee.objects.filter(election=election).order_by('-updated_at').first()
        if committee and committee.status == 'approved':
            raise CommitteeError('This election already has an approved custody committee.', code='already_approved')

        if not committee:
            committee = StrongroomCommittee(election=election, nominated_by=actor)
        committee.nominated_by = actor
        committee.peer_ec = peer
        committee.peer_approved_at = None
        committee.peer_approved_by = None
        committee.nominee_full_name = name
        committee.nominee_phone = phone
        committee.nominee_email = email
        committee.nominee_key_hash = ''
        committee.nominee_key_expires_at = None
        committee.nominee_key_sent_at = None
        committee.status = 'submitted'
        committee.save()

        StrongroomCommitteeMember.objects.filter(committee=committee).delete()
        StrongroomCommitteeMember.objects.create(committee=committee, user=actor, role='main_ec')
        StrongroomCommitteeMember.objects.create(committee=committee, user=peer, role='peer_ec')

        CustodyRecord.objects.create(
            election=election,
            action='committee_nominated',
            actor=actor,
            metadata={
                'committee_uuid': str(committee.uuid),
                'peer_ec_uuid': str(peer.uuid),
                'nominee_name': name,
                'nominee_phone_masked': phone[-4:] if len(phone) >= 4 else '****',
            },
        )
    return committee


def approve_committee(*, election, actor: User) -> StrongroomCommittee:
    committee = StrongroomCommittee.objects.filter(election=election).order_by('-updated_at').first()
    if not committee:
        raise CommitteeError('No committee nomination found.', status=404)
    if committee.status not in ('submitted', 'draft'):
        raise CommitteeError(f'Committee cannot be approved from status={committee.status}')
    if not committee.peer_ec_id:
        raise CommitteeError('Committee is missing a peer EC.')
    if actor.pk != committee.peer_ec_id and actor.pk != committee.nominated_by_id:
        # Only the designated peer may approve (nominating EC already counted as first).
        raise CommitteeError('Only the designated peer EC can approve this committee.', code='forbidden', status=403)
    if actor.pk == committee.nominated_by_id:
        raise CommitteeError('The nominating EC cannot self-approve. The peer EC must confirm.', code='forbidden', status=403)

    with transaction.atomic():
        committee.status = 'approved'
        committee.peer_approved_by = actor
        committee.peer_approved_at = timezone.now()
        committee.save(update_fields=[
            'status', 'peer_approved_by', 'peer_approved_at', 'updated_at',
        ])
        CustodyRecord.objects.create(
            election=election,
            action='committee_approved',
            actor=actor,
            metadata={'committee_uuid': str(committee.uuid)},
        )
        issue_nominee_key(committee)

    return committee


def serialize_committee(committee: StrongroomCommittee) -> dict:
    from strongroom.serializers import StrongroomCommitteeSerializer
    return StrongroomCommitteeSerializer(committee).data


def start_unlock_challenge(*, actor: User, password: str, election=None) -> dict:
    if not password or not actor.check_password(password):
        raise CommitteeError('Invalid credentials.', code='invalid_credentials', status=403)

    committee_qs = StrongroomCommittee.objects.filter(status='approved')
    if election:
        committee_qs = committee_qs.filter(election=election)
    committee = committee_qs.order_by('-updated_at').first()
    if not committee:
        raise CommitteeError(
            'Vault opens after a custody committee is approved.',
            code='committee_required',
            status=403,
        )

    # Initiator must be one of the two ECs on the committee.
    if actor.pk not in {committee.nominated_by_id, committee.peer_ec_id}:
        raise CommitteeError('Only the two committee ECs can open the audit vault.', code='forbidden', status=403)

    VaultUnlockChallenge.objects.filter(
        committee=committee,
        status__in=['awaiting_peer', 'awaiting_nominee'],
    ).update(status='cancelled', updated_at=timezone.now())

    challenge = VaultUnlockChallenge.objects.create(
        election=election or committee.election,
        committee=committee,
        status='awaiting_peer',
        initiated_by=actor,
        expires_at=timezone.now() + timedelta(minutes=UNLOCK_CHALLENGE_TTL_MINUTES),
    )
    CustodyRecord.objects.create(
        election=challenge.election,
        action='vault_unlock_started',
        actor=actor,
        metadata={'challenge_uuid': str(challenge.uuid)},
    )
    return serialize_challenge(challenge, actor)


def confirm_unlock_peer(*, actor: User, challenge_uuid) -> dict:
    challenge = VaultUnlockChallenge.objects.select_related('committee').filter(uuid=challenge_uuid).first()
    if not challenge:
        raise CommitteeError('Unlock challenge not found.', status=404)
    _ensure_challenge_fresh(challenge)
    if challenge.status != 'awaiting_peer':
        raise CommitteeError(f'Challenge is not awaiting peer confirm (status={challenge.status}).')

    committee = challenge.committee
    expected_peer = (
        committee.peer_ec_id
        if challenge.initiated_by_id == committee.nominated_by_id
        else committee.nominated_by_id
    )
    if actor.pk != expected_peer:
        raise CommitteeError('Waiting for the other committee EC to confirm.', code='forbidden', status=403)

    challenge.peer_confirmed_by = actor
    challenge.peer_confirmed_at = timezone.now()
    challenge.status = 'awaiting_nominee'
    challenge.save(update_fields=['peer_confirmed_by', 'peer_confirmed_at', 'status', 'updated_at'])
    CustodyRecord.objects.create(
        election=challenge.election,
        action='vault_unlock_peer_confirmed',
        actor=actor,
        metadata={'challenge_uuid': str(challenge.uuid)},
    )
    return serialize_challenge(challenge, actor)


def complete_unlock_with_nominee_key(*, actor: User, challenge_uuid, nominee_key: str, request=None) -> dict:
    challenge = VaultUnlockChallenge.objects.select_related('committee').filter(uuid=challenge_uuid).first()
    if not challenge:
        raise CommitteeError('Unlock challenge not found.', status=404)
    _ensure_challenge_fresh(challenge)
    if challenge.status != 'awaiting_nominee':
        raise CommitteeError('Challenge is not awaiting the nominee key.')

    # Either EC may enter the nominee key once peer has confirmed.
    if actor.pk not in {challenge.committee.nominated_by_id, challenge.committee.peer_ec_id}:
        raise CommitteeError('Only committee ECs can complete unlock.', code='forbidden', status=403)

    if not verify_nominee_key(challenge.committee, nominee_key or ''):
        raise CommitteeError('Invalid or expired nominee key.', code='invalid_key', status=403)

    token, session = create_vault_session(actor, request)
    challenge.nominee_verified_at = timezone.now()
    challenge.status = 'open'
    challenge.access_session = session
    challenge.save(update_fields=['nominee_verified_at', 'status', 'access_session', 'updated_at'])
    CustodyRecord.objects.create(
        election=challenge.election,
        action='vault_unlock_completed',
        actor=actor,
        metadata={'challenge_uuid': str(challenge.uuid), 'session_uuid': str(session.uuid)},
    )
    payload = serialize_challenge(challenge, actor)
    payload.update({
        'vault_token': token,
        'session_uuid': str(session.uuid),
        'expires_at': session.expires_at.isoformat(),
        'ttl_minutes': VAULT_SESSION_TTL_MINUTES,
        'message': 'Audit vault unlocked',
    })
    return payload


def _ensure_challenge_fresh(challenge: VaultUnlockChallenge):
    if challenge.status in ('expired', 'cancelled'):
        raise CommitteeError('This unlock challenge is no longer active.')
    if challenge.expires_at <= timezone.now():
        challenge.status = 'expired'
        challenge.save(update_fields=['status', 'updated_at'])
        raise CommitteeError('Unlock challenge expired. Start again.', code='expired')


def serialize_challenge(challenge: VaultUnlockChallenge, viewer: User | None = None) -> dict:
    committee = challenge.committee
    return {
        'uuid': str(challenge.uuid),
        'status': challenge.status,
        'election_uuid': str(challenge.election.uuid) if challenge.election_id else None,
        'election_title': challenge.election.title if challenge.election_id else None,
        'expires_at': challenge.expires_at.isoformat(),
        'initiated_by': {
            'uuid': str(challenge.initiated_by.uuid),
            'name': challenge.initiated_by.get_full_name() or challenge.initiated_by.email,
        },
        'peer_confirmed': bool(challenge.peer_confirmed_at),
        'nominee_name': committee.nominee_full_name,
        'nominee_key_expires_at': (
            committee.nominee_key_expires_at.isoformat() if committee.nominee_key_expires_at else None
        ),
        'steps': [
            {'key': 'ec_password', 'label': 'EC password', 'done': True},
            {'key': 'peer_confirm', 'label': 'Peer EC confirm', 'done': challenge.status in ('awaiting_nominee', 'open')},
            {'key': 'nominee_key', 'label': 'Nominee key', 'done': challenge.status == 'open'},
        ],
    }


def active_unlock_for_viewer(viewer: User) -> VaultUnlockChallenge | None:
    return (
        VaultUnlockChallenge.objects.select_related('committee', 'election', 'initiated_by')
        .filter(
            status__in=['awaiting_peer', 'awaiting_nominee'],
            expires_at__gt=timezone.now(),
        )
        .filter(
            models_q_committee_member(viewer),
        )
        .order_by('-created_at')
        .first()
    )


def models_q_committee_member(viewer: User):
    from django.db.models import Q
    return Q(committee__nominated_by=viewer) | Q(committee__peer_ec=viewer)
