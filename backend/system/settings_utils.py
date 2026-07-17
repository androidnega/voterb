from system.models import SystemSetting


DEFAULTS = {
    'otp_length': 6,
    'otp_expiry_minutes': 5,
    'svt_expiry_minutes': 20,
    'svt_max_requests_total': 3,
    'svt_max_requests_per_hour': 3,
    'svt_resend_cooldown_seconds': 60,
    'svt_max_validation_attempts': 5,
    'svt_cross_user_block_minutes': 60,
    'session_timeout_minutes': 30,
    'max_login_attempts': 5,
    'ussd_enabled': 'true',
    'ussd_service_code': '*920#',
    'ussd_session_timeout': 300,
    'ussd_retry_attempts': 3,
    'ussd_rate_limit_per_minute': 10,
}


def get_setting(key, default=None):
    setting = SystemSetting.objects.filter(key=key).first()
    if setting is None:
        return DEFAULTS.get(key, default)
    return setting.value


def get_setting_int(key, default=None):
    fallback = DEFAULTS.get(key, default if default is not None else 0)
    raw = get_setting(key, fallback)
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return int(fallback)


def get_setting_bool(key, default=False):
    fallback = DEFAULTS.get(key, default)
    raw = get_setting(key, fallback)
    if isinstance(raw, bool):
        return raw
    return str(raw).strip().lower() in ('1', 'true', 'yes', 'on')
