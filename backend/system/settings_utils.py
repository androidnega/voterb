from system.models import SystemSetting


DEFAULTS = {
    'otp_length': 6,
    'otp_expiry_minutes': 5,
    'svt_expiry_minutes': 10,
    'svt_max_requests_per_hour': 5,
    'svt_resend_cooldown_seconds': 60,
    'svt_max_validation_attempts': 5,
    'session_timeout_minutes': 30,
    'max_login_attempts': 5,
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
