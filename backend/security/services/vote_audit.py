"""Vote-cast audit capture — device, location, IP. Never records ballot choices."""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from security.models import AuditLog, DeviceLog, LocationLog

# Event types that belong on the voter audit trail (not auth/login).
VOTER_AUDIT_EVENTS = frozenset({'vote_cast'})

# Keys that must never be persisted or returned in audit metadata.
_BALLOT_SECRET_KEY_RE = re.compile(
    r'(candidate|selection|choice|ballot_choice|voted_for|vote_for)',
    re.IGNORECASE,
)


def client_ip(request) -> str | None:
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip() or None
    return request.META.get('REMOTE_ADDR')


def client_user_agent(request, client_context: dict | None = None) -> str:
    if isinstance(client_context, dict):
        ua = (client_context.get('user_agent') or '').strip()
        if ua:
            return ua[:2000]
    return (request.META.get('HTTP_USER_AGENT') or '')[:2000]


def sanitize_audit_metadata(metadata: dict | None) -> dict:
    """Strip anything that could reveal who someone voted for."""
    if not isinstance(metadata, dict):
        return {}

    clean = {}
    for key, value in metadata.items():
        if _BALLOT_SECRET_KEY_RE.search(str(key)):
            continue
        if key in {'selections', 'votes_created', 'candidates', 'candidate_uuids'}:
            continue
        if isinstance(value, dict):
            nested = sanitize_audit_metadata(value)
            if nested:
                clean[key] = nested
        elif isinstance(value, list):
            # Never keep lists that might be candidate UUIDs / names
            if key in {'positions', 'position_titles'}:
                # Allow count-only style: skip raw title lists that aren't needed
                continue
            clean[key] = [
                sanitize_audit_metadata(item) if isinstance(item, dict) else item
                for item in value
                if not isinstance(item, dict) or sanitize_audit_metadata(item) is not None
            ]
        else:
            clean[key] = value
    return clean


def _decimal_or_none(value):
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _normalize_client_context(raw) -> dict:
    if not isinstance(raw, dict):
        return {}
    allowed = {
        'fingerprint',
        'device_type',
        'operating_system',
        'platform',
        'platform_version',
        'architecture',
        'bitness',
        'model',
        'browser_name',
        'browser_version',
        'user_agent',
        'languages',
        'timezone',
        'screen',
        'hardware_concurrency',
        'device_memory_gb',
        'touch_points',
        'location',
        'hints_source',
    }
    out = {}
    for key in allowed:
        if key not in raw:
            continue
        val = raw[key]
        if key == 'location' and isinstance(val, dict):
            out[key] = {
                'latitude': val.get('latitude'),
                'longitude': val.get('longitude'),
                'accuracy': val.get('accuracy'),
            }
        elif key == 'screen' and isinstance(val, dict):
            out[key] = {
                'width': val.get('width') or val.get('w'),
                'height': val.get('height') or val.get('h'),
                'dpr': val.get('dpr'),
            }
        elif key == 'languages' and isinstance(val, list):
            out[key] = [str(x)[:32] for x in val[:8]]
        elif isinstance(val, (str, int, float, bool)) or val is None:
            if isinstance(val, str):
                out[key] = val[:500]
            else:
                out[key] = val
    return sanitize_audit_metadata(out)


def upsert_device_log(user, *, fingerprint: str, device_type: str, operating_system: str, user_agent: str):
    fp = (fingerprint or '').strip()
    if not fp:
        base = f'{user_agent}|{operating_system}|{device_type}|{getattr(user, "pk", "")}'
        fp = hashlib.sha256(base.encode('utf-8')).hexdigest()
    fp = fp[:128]

    device, _created = DeviceLog.objects.update_or_create(
        user=user,
        browser_fingerprint=fp,
        defaults={
            'device_type': (device_type or '')[:20],
            'operating_system': (operating_system or '')[:50],
            'user_agent': (user_agent or '')[:2000],
            'last_seen_at': timezone.now(),
        },
    )
    return device


def upsert_location_log(ip_address: str | None, client_location: dict | None = None):
    if not ip_address:
        return None

    loc_data = client_location if isinstance(client_location, dict) else {}
    lat = _decimal_or_none(loc_data.get('latitude'))
    lng = _decimal_or_none(loc_data.get('longitude'))

    defaults = {
        'last_seen_at': timezone.now(),
    }
    if lat is not None:
        defaults['latitude'] = lat
    if lng is not None:
        defaults['longitude'] = lng

    location, created = LocationLog.objects.get_or_create(
        ip_address=ip_address,
        defaults=defaults,
    )
    if not created:
        update_fields = ['last_seen_at']
        location.last_seen_at = timezone.now()
        if lat is not None:
            location.latitude = lat
            update_fields.append('latitude')
        if lng is not None:
            location.longitude = lng
            update_fields.append('longitude')
        location.save(update_fields=update_fields)
    return location


def record_vote_cast_audit(
    *,
    request,
    user,
    election,
    confirmation_code: str,
    positions_count: int,
    presence_capture=None,
    client_context=None,
) -> AuditLog:
    """
    Persist a vote_cast audit row with device/location context.
    Does not accept or store candidate / selection data.
    """
    ctx = _normalize_client_context(client_context)
    ip = client_ip(request)
    ua = client_user_agent(request, ctx)

    os_label = (
        ctx.get('operating_system')
        or ' '.join(
            str(x) for x in (ctx.get('platform'), ctx.get('platform_version')) if x
        ).strip()
        or _guess_os_from_ua(ua)
    )
    device_type = (ctx.get('device_type') or _guess_device_type(ua, ctx))[:20]
    fingerprint = (ctx.get('fingerprint') or '')[:128]

    device = upsert_device_log(
        user,
        fingerprint=fingerprint,
        device_type=device_type,
        operating_system=os_label[:50],
        user_agent=ua,
    )
    location = upsert_location_log(ip, ctx.get('location'))

    presence_id = None
    if presence_capture is not None:
        presence_id = getattr(presence_capture, 'uuid', None) or getattr(presence_capture, 'pk', None)

    metadata = sanitize_audit_metadata({
        'confirmation_code': confirmation_code,
        'positions_completed': int(positions_count or 0),
        'channel': 'web',
        'presence_capture_id': str(presence_id) if presence_id else None,
        'device': {
            'fingerprint': device.browser_fingerprint,
            'device_type': device.device_type,
            'operating_system': device.operating_system,
            'browser_name': ctx.get('browser_name'),
            'browser_version': ctx.get('browser_version'),
            'platform': ctx.get('platform'),
            'platform_version': ctx.get('platform_version'),
            'architecture': ctx.get('architecture'),
            'hints_source': ctx.get('hints_source') or 'user_agent',
            'timezone': ctx.get('timezone'),
            'languages': ctx.get('languages'),
            'screen': ctx.get('screen'),
            'hardware_concurrency': ctx.get('hardware_concurrency'),
            'device_memory_gb': ctx.get('device_memory_gb'),
            'touch_points': ctx.get('touch_points'),
        },
        'location': {
            'ip_address': ip,
            'latitude': float(location.latitude) if location and location.latitude is not None else (
                (ctx.get('location') or {}).get('latitude')
            ),
            'longitude': float(location.longitude) if location and location.longitude is not None else (
                (ctx.get('location') or {}).get('longitude')
            ),
            'accuracy_m': (ctx.get('location') or {}).get('accuracy'),
            'country': location.country if location else '',
            'region': location.region if location else '',
            'city': location.city if location else '',
        },
    })

    return AuditLog.objects.create(
        user=user,
        election=election,
        device_log=device,
        location_log=location,
        event_type='vote_cast',
        ip_address=ip,
        user_agent=ua,
        metadata=metadata,
        presence_capture_id=presence_id,
    )


def _guess_os_from_ua(ua: str) -> str:
    ua_l = (ua or '').lower()
    if 'android' in ua_l:
        return 'Android'
    if 'iphone' in ua_l or 'ipad' in ua_l or 'ios' in ua_l:
        return 'iOS'
    if 'mac os x' in ua_l or 'macintosh' in ua_l:
        return 'macOS'
    if 'windows' in ua_l:
        return 'Windows'
    if 'cros' in ua_l:
        return 'Chrome OS'
    if 'linux' in ua_l:
        return 'Linux'
    return 'Unknown'


def _guess_device_type(ua: str, ctx: dict) -> str:
    explicit = (ctx.get('device_type') or '').lower()
    if explicit in {'mobile', 'tablet', 'desktop'}:
        return explicit
    ua_l = (ua or '').lower()
    if 'ipad' in ua_l or 'tablet' in ua_l:
        return 'tablet'
    if 'mobi' in ua_l or 'iphone' in ua_l or 'android' in ua_l:
        return 'mobile'
    return 'desktop'
