"""USSD voting state machine — index → SVT → ballot (no photo), with resume + voted lockout."""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from candidates.models import Candidate
from elections.models import Election, Position, VotingChannel
from security.models import SVTToken
from system.settings_utils import get_setting, get_setting_bool, get_setting_int
from ussd.models import USSDSession
from ussd.services.ussd_auth import (
    is_valid_index_format,
    msisdn_already_voted,
    normalize_index,
    normalize_msisdn,
    resolve_index_candidates,
)
from voting.models import Vote

# Steps
STEP_ENTER_INDEX = 'enter_index'
STEP_SELECT_ELECTION = 'select_election'
STEP_ENTER_SVT = 'enter_svt'
STEP_SELECT_POSITION = 'select_position'
STEP_SELECT_CANDIDATE = 'select_candidate'
STEP_CONFIRM = 'confirm'
STEP_DONE = 'done'

RESUMABLE_STEPS = frozenset({
    STEP_ENTER_SVT,
    STEP_SELECT_ELECTION,
    STEP_SELECT_POSITION,
    STEP_SELECT_CANDIDATE,
    STEP_CONFIRM,
})

SVT_PATTERN = re.compile(r'^v-[a-z]{3}-\d{4}$', re.IGNORECASE)


@dataclass
class FlowResult:
    response: str
    outcome: str
    session: USSDSession


def con(message: str) -> str:
    return f'CON {message}'


def end(message: str) -> str:
    return f'END {message}'


def _service_code() -> str:
    return str(get_setting('ussd_service_code', '*920#') or '*920#').strip()


def _timeout_seconds(step: str | None = None) -> int:
    """SVT wait sessions stay alive much longer so voters can leave and return."""
    if step == STEP_ENTER_SVT:
        return max(600, get_setting_int('ussd_svt_resume_seconds', 7200))
    return max(120, get_setting_int('ussd_session_timeout', 1800))


def _retry_attempts() -> int:
    return max(1, get_setting_int('ussd_retry_attempts', 3))


def _is_channel_enabled() -> bool:
    if not get_setting_bool('ussd_enabled', True):
        return False
    try:
        from system.models import FeatureFlag
        flag = FeatureFlag.objects.filter(key='ussd_voting').first()
        if flag is not None and not flag.is_enabled:
            return False
    except Exception:
        pass
    return True


def _normalize_payload(data: dict) -> dict:
    session_id = (
        data.get('sessionId')
        or data.get('sessionID')
        or data.get('session_id')
        or data.get('session')
        or data.get('session_id'.upper())
        or ''
    )
    msisdn = (
        data.get('msisdn')
        or data.get('phoneNumber')
        or data.get('phone_number')
        or data.get('mobile')
        or data.get('subscriber')
        or ''
    )
    text = data.get('text')
    if text is None:
        text = (
            data.get('userData')
            if data.get('userData') is not None
            else data.get('message') if data.get('message') is not None else ''
        )
    new_session = data.get('newSession')
    if new_session is None:
        new_session = str(data.get('type', '')).lower() == 'initiation'
    if isinstance(new_session, str):
        new_session = new_session.strip().lower() in ('1', 'true', 'yes', 'y', 'initiation', 'new')
    return {
        'session_id': str(session_id).strip(),
        'msisdn': normalize_msisdn(str(msisdn).strip()) or str(msisdn).strip(),
        'text': str(text).strip() if text is not None else '',
        'new_session': bool(new_session),
        'service_code': str(data.get('serviceCode') or data.get('service_code') or '').strip(),
        'raw': data,
    }


def _latest_input(text: str, new_session: bool) -> str:
    raw = (text or '').strip()
    service = _service_code()
    if new_session or not raw or raw in (service, service.rstrip('#'), '*920#', '*920'):
        return ''
    parts = [p for p in raw.split('*') if p != '']
    if not parts:
        return ''
    last = parts[-1].rstrip('#')
    if last in ('920', service.strip('*#')):
        return ''
    return last


def _session_expired(session: USSDSession) -> bool:
    age = (timezone.now() - session.updated_at).total_seconds()
    return age > _timeout_seconds(session.current_step)


def get_or_create_session(msisdn: str, provider_session_id: str) -> USSDSession:
    qs = USSDSession.objects.filter(status='active')
    session = None
    if provider_session_id:
        session = qs.filter(provider_session_id=provider_session_id).first()
    if session is None and msisdn:
        session = qs.filter(msisdn=msisdn).order_by('-updated_at').first()
        if session and provider_session_id:
            session.provider_session_id = provider_session_id
            session.save(update_fields=['provider_session_id', 'updated_at'])

    if session and _session_expired(session):
        session.status = 'expired'
        session.save(update_fields=['status', 'updated_at'])
        session = None

    if session is None:
        session = USSDSession.objects.create(
            msisdn=msisdn,
            provider_session_id=provider_session_id or '',
            current_step=STEP_ENTER_INDEX,
            state_data={},
            status='active',
        )
    return session


def _save_step(session: USSDSession, step: str, **state_updates):
    data = dict(session.state_data or {})
    data.update({k: v for k, v in state_updates.items() if v is not None})
    # Drop keys explicitly set to None? keep simple
    for k, v in state_updates.items():
        if v is None and k in data:
            data.pop(k, None)
    session.current_step = step
    session.state_data = data
    session.save(update_fields=['current_step', 'state_data', 'updated_at', 'user', 'election', 'status'])


def open_positions_for_user(election: Election, user):
    voted_position_ids = set(
        Vote.objects.filter(user=user, election=election).values_list('position_id', flat=True)
    )
    positions = list(
        Position.objects.filter(
            election=election,
            is_active=True,
            is_votable=True,
        )
        .exclude(pk__in=voted_position_ids)
        .prefetch_related('restricted_categories')
        .order_by('display_order', 'title')
    )
    return [pos for pos in positions if pos.voter_may_see(user)]


def _welcome() -> str:
    return con(
        'Welcome to VoteBridge\n'
        'Enter your INDEX NUMBER:'
    )


def _resume_prompt(session: USSDSession) -> str:
    step = session.current_step
    title = (session.election.title if session.election_id else 'your ballot')[:40]
    if step == STEP_ENTER_SVT:
        return con(
            f'Welcome back\n'
            f'{title}\n'
            f'Enter the SVT sent to your phone\n'
            f'(format v-xxx-0000)\n'
            f'0. Restart'
        )
    if step == STEP_SELECT_POSITION:
        return _menu_positions(open_positions_for_user(session.election, session.user))
    if step == STEP_SELECT_CANDIDATE:
        state = session.state_data or {}
        position = Position.objects.filter(uuid=state.get('position_uuid')).first()
        if position:
            candidates = list(
                Candidate.objects.filter(position=position, status='approved')
                .order_by('ballot_number', 'full_name')
            )
            return _menu_candidates(candidates, position.title)
    if step == STEP_CONFIRM:
        state = session.state_data or {}
        return _confirm_prompt(state.get('candidate_name') or 'candidate', state.get('position_title') or 'position')
    if step == STEP_SELECT_ELECTION:
        options = (session.state_data or {}).get('election_options') or []
        return _menu_elections_from_options(options)
    return _welcome()


def _menu_elections_from_options(options) -> str:
    lines = ['Select election:']
    for i, o in enumerate(options, start=1):
        lines.append(f'{i}. {o.get("title")}')
    lines.append('0. Exit')
    return con('\n'.join(lines))


def _menu_positions(positions) -> str:
    if not positions:
        return end('You have already voted for all positions. Thank you.')
    lines = ['Select position:']
    for idx, pos in enumerate(positions, start=1):
        lines.append(f'{idx}. {pos.title}')
    lines.append('0. Exit')
    return con('\n'.join(lines))


def _menu_candidates(candidates, position_title: str) -> str:
    lines = [f'{position_title}', 'Select candidate:']
    for c in candidates:
        number = c.ballot_number if c.ballot_number is not None else '—'
        lines.append(f'{number}. {c.full_name}')
    lines.append('0. Back')
    return con('\n'.join(lines))


def _confirm_prompt(candidate_name: str, position_title: str) -> str:
    return con(
        f'Confirm vote\n'
        f'{position_title}: {candidate_name}\n'
        f'1. Yes\n'
        f'2. No'
    )


def _issue_svt_for_ussd(user, election: Election, dialing_msisdn: str | None = None) -> tuple[SVTToken | None, str | None, str | None]:
    """Issue SVT + realtime SMS to the phone on the voter record. Returns (svt, plaintext_or_None, error_or_None)."""
    from notifications.sms import mask_phone
    from notifications.tasks import dispatch_svt_sms
    from voting.api.views import (
        generate_svt,
        hash_svt,
        _svt_issue_expires_at,
        _svt_max_requests,
        _svt_request_count_total,
        _revoke_open_svts,
        _resolve_voter_phone,
    )

    if _svt_request_count_total(user, election) >= _svt_max_requests():
        return None, None, 'SVT request limit reached. Contact the EC.'

    phone = _resolve_voter_phone(user, election, preferred_msisdn=dialing_msisdn)
    if not phone:
        return None, None, 'No phone on your voter record. Contact the EC.'

    _revoke_open_svts(user, election)
    code = generate_svt()
    expires_at = _svt_issue_expires_at()
    svt = SVTToken.objects.create(
        user=user,
        election=election,
        token_hash=hash_svt(code),
        status='issued',
        expires_at=expires_at,
    )
    sms = dispatch_svt_sms(
        phone=phone,
        code=code,
        election_title=election.title,
        election_uuid=str(election.uuid),
        user_uuid=str(user.uuid),
    )
    if not sms.get('ok'):
        # Do not leave a usable token when SMS never left the platform.
        svt.status = 'revoked'
        svt.save(update_fields=['status'])
        return None, None, sms.get('error') or 'Could not send SVT SMS. Try again.'
    return svt, code, None


def _validate_svt_code(user, election: Election, raw_code: str) -> tuple[SVTToken | None, str | None]:
    from voting.api.views import hash_svt, _svt_validated_expires_at, normalize_svt

    code = normalize_svt(raw_code)
    if not SVT_PATTERN.fullmatch(code or ''):
        return None, 'Invalid SVT. Use format v-xxx-0000'

    token_hash = hash_svt(code)
    svt = (
        SVTToken.objects.filter(
            user=user,
            election=election,
            token_hash=token_hash,
            status='issued',
        )
        .order_by('-issued_at')
        .first()
    )
    if not svt:
        validated = (
            SVTToken.objects.filter(
                user=user,
                election=election,
                token_hash=token_hash,
                status='validated',
            )
            .order_by('-validated_at')
            .first()
        )
        if validated and validated.expires_at > timezone.now():
            return validated, None
        return None, 'SVT not recognised. Check SMS and try again.'

    if timezone.now() > svt.expires_at:
        svt.status = 'expired'
        svt.save(update_fields=['status'])
        return None, 'SVT expired. Dial again to request a new one.'

    svt.status = 'validated'
    svt.validated_at = timezone.now()
    svt.expires_at = _svt_validated_expires_at(election)
    svt.save(update_fields=['status', 'validated_at', 'expires_at'])
    return svt, None


def _active_validated_svt(user, election):
    return (
        SVTToken.objects.filter(
            user=user,
            election=election,
            status='validated',
            expires_at__gt=timezone.now(),
        )
        .order_by('-validated_at')
        .first()
    )


def _bind_election(session: USSDSession, user, election: Election) -> FlowResult:
    if Vote.objects.filter(user=user, election=election).exists() and not open_positions_for_user(election, user):
        session.user = user
        session.election = election
        session.status = 'completed'
        _save_step(session, STEP_DONE, ballot_complete=True)
        return FlowResult(end('You have already voted. Thank you.'), 'completed', session)

    session.user = user
    session.election = election

    validated = _active_validated_svt(user, election)
    if validated:
        _save_step(session, STEP_SELECT_POSITION, svt_id=str(validated.svt_id), svt_validated=True)
        return FlowResult(_menu_positions(open_positions_for_user(election, user)), 'continue', session)

    svt, _code, err = _issue_svt_for_ussd(user, election, dialing_msisdn=session.msisdn)
    if err and not svt:
        session.status = 'error'
        _save_step(session, STEP_DONE)
        return FlowResult(end(err), 'error', session)

    phone_hint = ''
    try:
        from voting.api.views import _resolve_voter_phone
        from notifications.sms import mask_phone
        phone = _resolve_voter_phone(user, election, preferred_msisdn=session.msisdn)
        if phone:
            phone_hint = f'\nSent to {mask_phone(phone)}'
    except Exception:
        phone_hint = ''

    _save_step(
        session,
        STEP_ENTER_SVT,
        svt_id=str(svt.svt_id) if svt else None,
        index_attempts=0,
    )
    msg = (
        f'SVT sent by SMS{phone_hint}\n'
        f'Enter your SVT now\n'
        f'(or hang up and dial again later)\n'
        f'Format: v-xxx-0000\n'
        f'0. Resend SVT'
    )
    if err:
        msg = f'{err}\nEnter SVT if received, or 0 to resend:'
    return FlowResult(con(msg), 'continue', session)


def _cast_ussd_vote(user, election: Election, position: Position, candidate: Candidate, *, msisdn: str = '', ip_address: str | None = None, svt=None) -> str:
    if election.status != 'open' or not election.allow_ussd_voting:
        return end('This election is not open for USSD voting.')
    if not position.voter_may_see(user):
        return end('You are not eligible to vote for this position.')
    if Vote.objects.filter(user=user, position=position).exists():
        return end('You have already voted for this position.')
    if svt is None:
        svt = _active_validated_svt(user, election)
    if svt is None:
        return end('Validate your SVT first. Dial again to continue.')

    channel, _ = VotingChannel.objects.get_or_create(
        channel_name='ussd',
        defaults={'is_active': True},
    )
    vote_hash = hashlib.sha256(
        f'{user.uuid}{election.uuid}{position.uuid}{candidate.uuid}{timezone.now().isoformat()}ussd'.encode()
    ).hexdigest()
    with transaction.atomic():
        Vote.objects.create(
            user=user,
            election=election,
            position=position,
            candidate=candidate,
            channel=channel,
            svt=svt,
            vote_hash=vote_hash,
        )
        confirmation = f'VTB-U-{str(election.uuid)[:4].upper()}-{random.randint(100000, 999999)}'
        from security.services.vote_audit import record_vote_cast_audit
        from strongroom.services import seal_vote_cast
        from elections.ws import broadcast_election_monitor

        audit_log = record_vote_cast_audit(
            user=user,
            election=election,
            confirmation_code=confirmation,
            positions_count=1,
            channel='ussd',
            msisdn=msisdn,
            ip_address=ip_address,
        )
        seal_vote_cast(
            election=election,
            confirmation_code=confirmation,
            audit_log=audit_log,
            presence_capture=None,
            svt=svt,
            channel='ussd',
        )
    try:
        broadcast_election_monitor(election)
    except Exception:
        pass

    remaining = open_positions_for_user(election, user)
    if remaining:
        return con(
            f'Vote recorded.\n'
            f'Code: {confirmation}\n'
            f'Remaining positions:\n'
            + '\n'.join(f'{i}. {p.title}' for i, p in enumerate(remaining, start=1))
            + '\n0. Exit'
        )

    # Mark SVT used when ballot complete
    try:
        svt.status = 'used'
        svt.used_at = timezone.now()
        svt.expires_at = timezone.now()
        svt.save(update_fields=['status', 'used_at', 'expires_at'])
    except Exception:
        pass
    return end(f'Vote recorded. Thank you.\nCode: {confirmation}')


def process_ussd_request(payload: dict) -> FlowResult:
    parsed = _normalize_payload(payload or {})
    msisdn = parsed['msisdn']
    session_id = parsed['session_id']
    user_input = _latest_input(parsed['text'], parsed['new_session'])
    new_session = parsed['new_session']

    if not _is_channel_enabled():
        session = get_or_create_session(msisdn or 'unknown', session_id)
        session.status = 'error'
        session.save(update_fields=['status', 'updated_at'])
        return FlowResult(end('USSD voting is currently unavailable.'), 'disabled', session)

    if not msisdn:
        session = get_or_create_session('unknown', session_id)
        session.status = 'error'
        session.save(update_fields=['status', 'updated_at'])
        return FlowResult(end('Invalid request. Missing phone number.'), 'error', session)

    # Voted lockout — no index asked
    if msisdn_already_voted(msisdn):
        session = get_or_create_session(msisdn, session_id)
        session.status = 'completed'
        _save_step(session, STEP_DONE, ballot_complete=True)
        return FlowResult(
            end('You have already voted.\nThis number cannot vote again via USSD.\nThank you.'),
            'completed',
            session,
        )

    session = get_or_create_session(msisdn, session_id)
    gateway_ip = (payload or {}).get('_gateway_ip') or ''
    if gateway_ip:
        data = dict(session.state_data or {})
        if data.get('gateway_ip') != gateway_ip:
            data['gateway_ip'] = gateway_ip
            session.state_data = data
            session.save(update_fields=['state_data', 'updated_at'])

    # Fresh dial with empty input — resume mid-flow instead of restarting
    if not user_input and (new_session or session.current_step in ('', STEP_ENTER_INDEX, STEP_DONE)):
        if session.current_step in RESUMABLE_STEPS and session.user_id and session.election_id:
            return FlowResult(_resume_prompt(session), 'continue', session)
        # Legacy PIN step → migrate to index
        if session.current_step == 'enter_pin':
            _save_step(session, STEP_ENTER_INDEX)
        else:
            session.user = None
            session.election = None
            session.status = 'active'
            _save_step(session, STEP_ENTER_INDEX)
        return FlowResult(_welcome(), 'continue', session)

    if not user_input and session.current_step in RESUMABLE_STEPS:
        return FlowResult(_resume_prompt(session), 'continue', session)

    step = session.current_step or STEP_ENTER_INDEX
    if step == 'enter_pin':
        step = STEP_ENTER_INDEX
        _save_step(session, STEP_ENTER_INDEX)

    try:
        if step == STEP_ENTER_INDEX:
            return _handle_enter_index(session, user_input)
        if step == STEP_SELECT_ELECTION:
            return _handle_select_election(session, user_input)
        if step == STEP_ENTER_SVT:
            return _handle_enter_svt(session, user_input)
        if step == STEP_SELECT_POSITION:
            return _handle_select_position(session, user_input)
        if step == STEP_SELECT_CANDIDATE:
            return _handle_select_candidate(session, user_input)
        if step == STEP_CONFIRM:
            return _handle_confirm(session, user_input)
        _save_step(session, STEP_ENTER_INDEX)
        return FlowResult(_welcome(), 'continue', session)
    except Exception:
        session.status = 'error'
        session.save(update_fields=['status', 'updated_at'])
        return FlowResult(end('An error occurred. Please try again later.'), 'error', session)


def _handle_enter_index(session: USSDSession, user_input: str) -> FlowResult:
    if user_input == '0':
        session.status = 'completed'
        _save_step(session, STEP_DONE)
        return FlowResult(end('Goodbye.'), 'completed', session)

    if not is_valid_index_format(user_input):
        attempts = int((session.state_data or {}).get('index_attempts', 0)) + 1
        max_attempts = _retry_attempts()
        if attempts >= max_attempts:
            session.status = 'error'
            _save_step(session, STEP_DONE, index_attempts=attempts)
            return FlowResult(end('Too many invalid attempts. Session ended.'), 'denied', session)
        _save_step(session, STEP_ENTER_INDEX, index_attempts=attempts)
        return FlowResult(
            con(f'Invalid index. Enter your INDEX NUMBER:\n({attempts}/{max_attempts})'),
            'continue',
            session,
        )

    matches = resolve_index_candidates(user_input, session.msisdn)
    if not matches:
        attempts = int((session.state_data or {}).get('index_attempts', 0)) + 1
        max_attempts = _retry_attempts()
        if attempts >= max_attempts:
            session.status = 'error'
            _save_step(session, STEP_DONE, index_attempts=attempts)
            return FlowResult(end('Index not found for USSD voting. Session ended.'), 'denied', session)
        _save_step(session, STEP_ENTER_INDEX, index_attempts=attempts)
        return FlowResult(
            con(f'Index not found. Try again:\n({attempts}/{max_attempts})'),
            'continue',
            session,
        )

    options = [
        {
            'election_uuid': m['election_uuid'],
            'user_uuid': m['user_uuid'],
            'title': m['title'],
        }
        for m in matches
    ]

    if len(matches) == 1:
        return _bind_election(session, matches[0]['user'], matches[0]['election'])

    session.user = None
    session.election = None
    _save_step(session, STEP_SELECT_ELECTION, election_options=options, index_attempts=0, index=normalize_index(user_input))
    return FlowResult(_menu_elections_from_options(options), 'continue', session)


def _handle_select_election(session: USSDSession, user_input: str) -> FlowResult:
    if user_input == '0':
        session.status = 'completed'
        _save_step(session, STEP_DONE)
        return FlowResult(end('Goodbye.'), 'completed', session)

    options = (session.state_data or {}).get('election_options') or []
    try:
        idx = int(user_input) - 1
    except (TypeError, ValueError):
        return FlowResult(_menu_elections_from_options(options), 'continue', session)

    if idx < 0 or idx >= len(options):
        return FlowResult(_menu_elections_from_options(options), 'continue', session)

    choice = options[idx]
    election = Election.objects.filter(uuid=choice['election_uuid']).first()
    from accounts.models import User
    user = User.objects.filter(uuid=choice['user_uuid']).first()
    if not election or not user or election.status != 'open' or not election.allow_ussd_voting:
        return FlowResult(end('Election is not available for USSD voting.'), 'denied', session)
    return _bind_election(session, user, election)


def _handle_enter_svt(session: USSDSession, user_input: str) -> FlowResult:
    user = session.user
    election = session.election
    if not user or not election:
        _save_step(session, STEP_ENTER_INDEX)
        return FlowResult(_welcome(), 'continue', session)

    if user_input == '0':
        svt, _code, err = _issue_svt_for_ussd(user, election, dialing_msisdn=session.msisdn)
        if err and not svt:
            return FlowResult(con(f'{err}\n0. Try resend again\nOr enter SVT:'), 'continue', session)
        _save_step(session, STEP_ENTER_SVT, svt_id=str(svt.svt_id) if svt else None)
        return FlowResult(
            con('New SVT sent by SMS.\nEnter your SVT (v-xxx-0000):\n0. Resend again'),
            'continue',
            session,
        )

    if user_input == '9':
        # Restart identity
        session.user = None
        session.election = None
        _save_step(session, STEP_ENTER_INDEX)
        return FlowResult(_welcome(), 'continue', session)

    svt, err = _validate_svt_code(user, election, user_input)
    if err:
        attempts = int((session.state_data or {}).get('svt_attempts', 0)) + 1
        max_attempts = _retry_attempts()
        if attempts >= max_attempts:
            session.status = 'error'
            _save_step(session, STEP_DONE, svt_attempts=attempts)
            return FlowResult(end('Too many invalid SVT attempts. Session ended.'), 'denied', session)
        _save_step(session, STEP_ENTER_SVT, svt_attempts=attempts)
        return FlowResult(con(f'{err}\nTry again:\n0. Resend SVT'), 'continue', session)

    _save_step(session, STEP_SELECT_POSITION, svt_id=str(svt.svt_id), svt_validated=True, svt_attempts=0)
    return FlowResult(_menu_positions(open_positions_for_user(election, user)), 'continue', session)


def _handle_select_position(session: USSDSession, user_input: str) -> FlowResult:
    if user_input == '0':
        session.status = 'completed'
        _save_step(session, STEP_DONE)
        return FlowResult(end('Goodbye. Dial again to continue if needed.'), 'completed', session)

    election = session.election
    user = session.user
    if not election or not user:
        _save_step(session, STEP_ENTER_INDEX)
        return FlowResult(_welcome(), 'continue', session)
    if election.status != 'open':
        return FlowResult(end('Election is no longer open.'), 'denied', session)
    if not _active_validated_svt(user, election):
        _save_step(session, STEP_ENTER_SVT)
        return FlowResult(
            con('Your SVT session expired.\nEnter SVT from SMS, or 0 to resend:'),
            'continue',
            session,
        )

    positions = open_positions_for_user(election, user)
    try:
        idx = int(user_input) - 1
    except (TypeError, ValueError):
        return FlowResult(_menu_positions(positions), 'continue', session)

    if idx < 0 or idx >= len(positions):
        return FlowResult(_menu_positions(positions), 'continue', session)

    position = positions[idx]
    candidates = list(
        Candidate.objects.filter(position=position, status='approved').order_by('ballot_number', 'full_name')
    )
    if not candidates:
        return FlowResult(end('No candidates available for this position.'), 'error', session)

    _save_step(
        session,
        STEP_SELECT_CANDIDATE,
        position_uuid=str(position.uuid),
        position_title=position.title,
    )
    return FlowResult(_menu_candidates(candidates, position.title), 'continue', session)


def _handle_select_candidate(session: USSDSession, user_input: str) -> FlowResult:
    if user_input == '0':
        _save_step(session, STEP_SELECT_POSITION, candidate_uuid=None, candidate_name=None)
        return FlowResult(
            _menu_positions(open_positions_for_user(session.election, session.user)),
            'continue',
            session,
        )

    state = session.state_data or {}
    position = Position.objects.filter(uuid=state.get('position_uuid'), election=session.election).first()
    if not position:
        _save_step(session, STEP_SELECT_POSITION)
        return FlowResult(
            _menu_positions(open_positions_for_user(session.election, session.user)),
            'continue',
            session,
        )

    candidates = list(
        Candidate.objects.filter(position=position, status='approved').order_by('ballot_number', 'full_name')
    )
    selected = None
    try:
        number = int(user_input)
    except (TypeError, ValueError):
        return FlowResult(_menu_candidates(candidates, position.title), 'continue', session)

    for c in candidates:
        if c.ballot_number == number:
            selected = c
            break
    if selected is None and 1 <= number <= len(candidates):
        selected = candidates[number - 1]

    if selected is None:
        return FlowResult(
            con('Invalid candidate number.\n' + _menu_candidates(candidates, position.title)[4:]),
            'continue',
            session,
        )

    _save_step(
        session,
        STEP_CONFIRM,
        candidate_uuid=str(selected.uuid),
        candidate_name=selected.full_name,
        position_title=position.title,
        position_uuid=str(position.uuid),
    )
    return FlowResult(_confirm_prompt(selected.full_name, position.title), 'continue', session)


def _handle_confirm(session: USSDSession, user_input: str) -> FlowResult:
    if user_input == '2':
        _save_step(session, STEP_SELECT_POSITION, candidate_uuid=None, candidate_name=None)
        return FlowResult(
            _menu_positions(open_positions_for_user(session.election, session.user)),
            'continue',
            session,
        )

    if user_input != '1':
        name = (session.state_data or {}).get('candidate_name') or 'candidate'
        title = (session.state_data or {}).get('position_title') or 'position'
        return FlowResult(_confirm_prompt(name, title), 'continue', session)

    election = session.election
    user = session.user
    state = session.state_data or {}
    position = Position.objects.filter(uuid=state.get('position_uuid'), election=election).first()
    candidate = Candidate.objects.filter(uuid=state.get('candidate_uuid'), position=position).first()
    if not election or not user or not position or not candidate:
        session.status = 'error'
        _save_step(session, STEP_DONE)
        return FlowResult(end('Unable to record vote. Please start again.'), 'error', session)

    svt = _active_validated_svt(user, election)
    response = _cast_ussd_vote(
        user,
        election,
        position,
        candidate,
        msisdn=getattr(session, 'msisdn', '') or '',
        ip_address=(session.state_data or {}).get('gateway_ip') or None,
        svt=svt,
    )

    if response.startswith('END'):
        session.status = 'completed'
        _save_step(session, STEP_DONE, ballot_complete=True)
        return FlowResult(response, 'completed', session)

    _save_step(session, STEP_SELECT_POSITION, candidate_uuid=None, candidate_name=None, position_uuid=None)
    return FlowResult(response, 'continue', session)
