"""Outbound SMS helpers — Arkesel primary, Moolre fallback."""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request

from django.core.cache import cache

from django.conf import settings

from system.settings_utils import get_setting, get_setting_bool

logger = logging.getLogger(__name__)


def _is_debug() -> bool:
    return bool(getattr(settings, 'DEBUG', False))


def normalize_msisdn(phone: str) -> str | None:
    """Normalize Ghana-style numbers to E.164-ish digits for SMS gateways."""
    raw = (phone or '').strip()
    if not raw:
        return None
    digits = re.sub(r'[^\d+]', '', raw)
    if digits.startswith('+'):
        digits = digits[1:]
    digits = re.sub(r'\D', '', digits)
    if not digits:
        return None
    if digits.startswith('0') and len(digits) == 10:
        digits = f'233{digits[1:]}'
    if digits.startswith('233') and len(digits) >= 12:
        return digits
    if len(digits) >= 9:
        return digits
    return None


def mask_phone(phone: str) -> str:
    digits = re.sub(r'\D', '', phone or '')
    if len(digits) < 4:
        return '****'
    return f'***{digits[-4:]}'


# Cloudflare (and some SMS gateways) block Python's default urllib User-Agent.
_DEFAULT_SMS_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (compatible; VoteBridge/1.0; +https://votebridge.online) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'application/json',
}


def _with_sms_headers(headers: dict | None) -> dict:
    merged = dict(_DEFAULT_SMS_HEADERS)
    if headers:
        merged.update(headers)
    return merged


def _http_json_post(url: str, payload: dict, headers: dict, timeout: int = 20) -> tuple[bool, int, str]:
    body = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url, data=body, headers=_with_sms_headers(headers), method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = int(getattr(response, 'status', 200))
            text = response.read().decode('utf-8', errors='replace')
            return 200 <= status_code < 300, status_code, text
    except urllib.error.HTTPError as exc:
        text = exc.read().decode('utf-8', errors='replace') if exc.fp else ''
        return False, int(exc.code), text
    except Exception as exc:
        logger.warning('HTTP POST failed for %s: %s', url, exc)
        return False, 0, str(exc)


def _http_get(url: str, headers: dict | None = None, timeout: int = 20) -> tuple[bool, int, str]:
    req = urllib.request.Request(url, headers=_with_sms_headers(headers), method='GET')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = int(getattr(response, 'status', 200))
            text = response.read().decode('utf-8', errors='replace')
            return 200 <= status_code < 300, status_code, text
    except urllib.error.HTTPError as exc:
        text = exc.read().decode('utf-8', errors='replace') if exc.fp else ''
        return False, int(exc.code), text
    except Exception as exc:
        logger.warning('HTTP GET failed for %s: %s', url, exc)
        return False, 0, str(exc)


def _provider_detail(body: str, fallback: str) -> str:
    payload = _parse_json_body(body)
    for key in ('message', 'error', 'detail'):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    text = (body or '').strip()
    if text and len(text) <= 240:
        return text
    return fallback


def _local_gh_phone(msisdn: str) -> str:
    digits = re.sub(r'\D', '', msisdn or '')
    if digits.startswith('233') and len(digits) >= 12:
        return f'0{digits[3:]}'
    if digits.startswith('0'):
        return digits
    return digits


def _parse_json_body(body: str) -> dict:
    try:
        data = json.loads(body or '')
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _arkesel_accepted(status_code: int, body: str) -> bool:
    if not (200 <= status_code < 300):
        return False
    payload = _parse_json_body(body)
    status = str(payload.get('status') or '').strip().lower()
    if status and status not in ('success', 'ok', '1', 'true'):
        return False
    return True


def _moolre_accepted(status_code: int, body: str) -> bool:
    if not (200 <= status_code < 300):
        return False
    payload = _parse_json_body(body)
    if not payload:
        return True
    status = payload.get('status')
    if status in (0, '0', False, 'false', 'error', 'failed'):
        return False
    code = str(payload.get('code') or '').upper()
    if code and code.startswith('AI') and code != 'SMS01':
        # Auth / validation style codes from Moolre docs
        if code.startswith(('AIN', 'ASM')):
            return False
    return True


def _resolve_moolre_url(raw_url: str) -> str:
    """Prefer the current Moolre open SMS endpoint; rewrite legacy /v1 URLs."""
    url = (raw_url or '').strip() or 'https://api.moolre.com/open/sms/send'
    if '/v1/sms/send' in url:
        return 'https://api.moolre.com/open/sms/send'
    return url


def _send_arkesel(msisdn: str, message: str, masked: str, *, http_timeout: int = 20) -> dict:
    api_key = (get_setting('sms_arkesel_api_key') or get_setting('sms_api_key') or '').strip()
    sender = (get_setting('sms_arkesel_sender_id') or get_setting('sms_sender_id') or 'VoterB').strip()
    url = (get_setting('sms_arkesel_url') or 'https://sms.arkesel.com/api/v2/sms/send').strip()
    if not api_key:
        return {'ok': False, 'provider': 'arkesel', 'masked_phone': masked, 'error': 'Arkesel API key missing'}

    ok_http, status_code, body = _http_json_post(
        url,
        {'sender': sender, 'message': message, 'recipients': [msisdn]},
        {'api-key': api_key, 'Content-Type': 'application/json'},
        timeout=http_timeout,
    )
    if not ok_http or not _arkesel_accepted(status_code, body):
        detail = _provider_detail(body, 'Arkesel rejected the message')
        logger.error('Arkesel SMS failed (%s): %s', status_code, body[:300])
        return {
            'ok': False,
            'provider': 'arkesel',
            'masked_phone': masked,
            'error': detail,
            'status_code': status_code,
            'response': body[:500],
        }
    return {'ok': True, 'provider': 'arkesel', 'masked_phone': masked}


def _send_moolre_get(msisdn: str, message: str, masked: str, api_key: str, sender: str, *, http_timeout: int = 20) -> dict:
    base = _resolve_moolre_url('')
    params = urllib.parse.urlencode({
        'type': 1,
        'senderid': sender,
        'recipient': _local_gh_phone(msisdn) or msisdn,
        'message': message,
    })
    url = f'{base}?{params}'
    ok_http, status_code, body = _http_get(
        url,
        headers={'X-API-VASKEY': api_key, 'Accept': 'application/json'},
        timeout=http_timeout,
    )
    if ok_http and _moolre_accepted(status_code, body):
        return {'ok': True, 'provider': 'moolre', 'masked_phone': masked, 'transport': 'get'}
    detail = _provider_detail(body, 'Moolre GET rejected the message')
    logger.error('Moolre GET SMS failed (%s): %s', status_code, body[:300])
    return {
        'ok': False,
        'provider': 'moolre',
        'masked_phone': masked,
        'error': detail,
        'status_code': status_code,
        'response': body[:500],
    }


def _send_moolre(msisdn: str, message: str, masked: str, *, http_timeout: int = 20) -> dict:
    api_key = (get_setting('sms_moolre_api_key') or '').strip()
    sender = (get_setting('sms_moolre_sender_id') or get_setting('sms_sender_id') or 'VoterB').strip()[:11]
    url = _resolve_moolre_url(get_setting('sms_moolre_url') or '')
    if not api_key:
        return {'ok': False, 'provider': 'moolre', 'masked_phone': masked, 'error': 'Moolre API key missing'}

    ok_http, status_code, body = _http_json_post(
        url,
        {
            'type': 1,
            'senderid': sender,
            'messages': [
                {
                    'recipient': _local_gh_phone(msisdn) or msisdn,
                    'message': message,
                }
            ],
        },
        {
            'X-API-VASKEY': api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        timeout=http_timeout,
    )
    if ok_http and _moolre_accepted(status_code, body):
        return {'ok': True, 'provider': 'moolre', 'masked_phone': masked, 'transport': 'post'}

    post_detail = _provider_detail(body, 'Moolre POST rejected the message')
    logger.warning('Moolre POST SMS failed (%s): %s — trying GET fallback', status_code, body[:300])
    get_result = _send_moolre_get(msisdn, message, masked, api_key, sender, http_timeout=http_timeout)
    if get_result.get('ok'):
        get_result['fallback_used'] = True
        get_result['post_error'] = post_detail
        return get_result

    return {
        'ok': False,
        'provider': 'moolre',
        'masked_phone': masked,
        'error': get_result.get('error') or post_detail,
        'status_code': status_code,
        'response': body[:500],
    }


def send_sms(*, phone: str, message: str, cache_key: str | None = None, http_timeout: int = 20) -> dict:
    """
    Send SMS via primary provider (Arkesel), falling back to Moolre.
    Optional cache_key reuses a pre-warmed payload from Redis.
    """
    masked = mask_phone(phone)
    msisdn = normalize_msisdn(phone)
    if not msisdn:
        return {'ok': False, 'provider': None, 'masked_phone': masked, 'error': 'Invalid phone number'}

    if cache_key:
        cached = cache.get(cache_key)
        if isinstance(cached, dict) and cached.get('message'):
            message = cached['message']
            if cached.get('msisdn'):
                msisdn = cached['msisdn']

    enabled = get_setting_bool('sms_enabled', True)
    primary = (get_setting('sms_provider_primary') or get_setting('sms_provider') or 'arkesel').strip().lower()
    fallback = (get_setting('sms_provider_fallback') or 'moolre').strip().lower()

    if not enabled:
        # Dev may log; production must never pretend SMS was delivered.
        if _is_debug():
            logger.info('SMS disabled (DEBUG) — would send to %s: %s', masked, message)
            return {'ok': True, 'provider': 'disabled-log', 'masked_phone': masked, 'dev_logged': True}
        return {
            'ok': False,
            'provider': None,
            'masked_phone': masked,
            'error': 'SMS is disabled. Enable sms_enabled in system settings for production.',
        }

    providers = []
    if primary:
        providers.append(primary)
    if fallback and fallback not in providers:
        providers.append(fallback)
    # Always keep Moolre as a last-resort fallback for OTP / transactional SMS.
    if 'moolre' not in providers and (get_setting('sms_moolre_api_key') or '').strip():
        providers.append('moolre')
    if 'arkesel' not in providers and (
        (get_setting('sms_arkesel_api_key') or get_setting('sms_api_key') or '').strip()
    ):
        providers.append('arkesel')

    has_any_key = bool(
        (get_setting('sms_arkesel_api_key') or get_setting('sms_api_key') or '').strip()
        or (get_setting('sms_moolre_api_key') or '').strip()
    )
    if not has_any_key:
        if _is_debug():
            print(f'📱 SMS → {masked}: {message}')
            logger.warning('SMS API keys missing (DEBUG) — logged message for %s', masked)
            return {'ok': True, 'provider': 'console', 'masked_phone': masked, 'dev_logged': True}
        return {
            'ok': False,
            'provider': None,
            'masked_phone': masked,
            'error': (
                'SMS is not configured. Set Arkesel and/or Moolre API keys in system settings '
                'before going to production.'
            ),
        }

    last_error = None
    for name in providers:
        if name == 'arkesel':
            result = _send_arkesel(msisdn, message, masked, http_timeout=http_timeout)
        elif name == 'moolre':
            result = _send_moolre(msisdn, message, masked, http_timeout=http_timeout)
        else:
            continue
        if result.get('ok'):
            if name != primary:
                result['fallback_used'] = True
                result['primary'] = primary
            return result
        last_error = result

    return last_error or {
        'ok': False,
        'provider': primary,
        'masked_phone': masked,
        'error': 'All SMS providers failed',
    }


def send_svt_sms(*, phone: str, code: str, election_title: str, election_uuid: str | None = None, user_uuid: str | None = None) -> dict:
    title = (election_title or 'election')[:60]
    minutes = 20
    try:
        from system.settings_utils import get_setting_int
        minutes = max(1, get_setting_int('svt_expiry_minutes', 20))
    except Exception:
        minutes = 20

    cache_key = None
    if election_uuid and user_uuid:
        cache_key = f'sms:prewarm:election:{election_uuid}:user:{user_uuid}'

    message = (
        f'Your VoteBridge SVT for {title} is {code}. '
        f'Valid for {minutes} minutes. Do not share. One use only.'
    )
    # Prefer cached template body if pre-warmed (code still injected at send time).
    if cache_key:
        cached = cache.get(cache_key)
        if isinstance(cached, dict) and cached.get('template'):
            message = str(cached['template']).format(code=code, title=title, minutes=minutes)

    return send_sms(phone=phone, message=message, cache_key=None)


def prewarm_election_sms_payloads(election, *, hours_ahead: int = 5) -> dict:
    """
    Cache lightweight SMS templates for eligible voters in Redis so bulk send
    near open time does not rebuild messages from scratch.
    """
    from elections.services.register_service import election_register_entry_queryset

    ttl = max(3600, int(hours_ahead * 3600) + 1800)
    title = (election.title or 'election')[:60]
    minutes = 20
    try:
        from system.settings_utils import get_setting_int
        minutes = max(1, get_setting_int('svt_expiry_minutes', 20))
    except Exception:
        minutes = 20

    template = (
        'Your VoteBridge SVT for {title} is {code}. '
        'Valid for {minutes} minutes. Do not share. One use only.'
    )
    queued = 0
    skipped = 0
    entries = (
        election_register_entry_queryset(election)
        .select_related('user')
        .only('uuid', 'phone_number', 'user__uuid', 'user__phone_number')
    )
    for entry in entries.iterator(chunk_size=500):
        user = entry.user
        if not user:
            skipped += 1
            continue
        phone = (entry.phone_number or user.phone_number or '').strip()
        msisdn = normalize_msisdn(phone)
        if not msisdn:
            skipped += 1
            continue
        key = f'sms:prewarm:election:{election.uuid}:user:{user.uuid}'
        cache.set(
            key,
            {
                'msisdn': msisdn,
                'masked_phone': mask_phone(phone),
                'template': template,
                'title': title,
                'minutes': minutes,
                'election_uuid': str(election.uuid),
                'user_uuid': str(user.uuid),
            },
            timeout=ttl,
        )
        queued += 1
    return {'queued': queued, 'skipped': skipped, 'ttl_seconds': ttl}
