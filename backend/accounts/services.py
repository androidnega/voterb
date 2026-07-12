import hashlib
import random
import re
from datetime import timedelta

from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import OTPRequest, Session
from system.settings_utils import get_setting_int

OTP_PREFIX = 'rte-'


def normalize_otp(code):
    """Normalize to rte-<digits> regardless of how the user typed it."""
    raw = str(code or '').strip().lower().replace(' ', '')
    if raw.startswith(OTP_PREFIX):
        raw = raw[len(OTP_PREFIX):]
    digits = re.sub(r'\D', '', raw)
    if not digits:
        return ''
    return f'{OTP_PREFIX}{digits}'


def hash_otp(code):
    return hashlib.sha256(normalize_otp(code).encode()).hexdigest()


class OTPService:
    @staticmethod
    def create_otp(user, purpose='login', channel='sms'):
        """Generate OTP as rte-<digits>, hash it, store, and return the request."""
        length = max(4, min(8, get_setting_int('otp_length', 6)))
        upper = 10 ** length
        lower = 10 ** (length - 1)
        digits = f'{random.randint(lower, upper - 1)}'
        code = f'{OTP_PREFIX}{digits}'
        hashed = hash_otp(code)
        expiry_minutes = max(1, get_setting_int('otp_expiry_minutes', 5))
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        otp = OTPRequest.objects.create(
            user=user,
            purpose=purpose,
            channel=channel,
            otp_hash=hashed,
            expires_at=expires_at,
        )
        print(f'🔑 OTP for {user.email or user.index_number}: {code}')
        return otp

    @staticmethod
    def verify_otp(otp_uuid, code):
        """Verify OTP: return user if valid, else None."""
        try:
            otp = OTPRequest.objects.get(uuid=otp_uuid, is_verified=False)
        except OTPRequest.DoesNotExist:
            return None
        if timezone.now() > otp.expires_at:
            return None
        normalized = normalize_otp(code)
        if not normalized:
            return None
        if hash_otp(normalized) == otp.otp_hash:
            otp.is_verified = True
            otp.verified_at = timezone.now()
            otp.save(update_fields=['is_verified', 'verified_at'])
            return otp.user
        return None


class SessionService:
    @staticmethod
    def create_session(user, request):
        """Create a JWT refresh token, store session, return access+refresh tokens."""
        refresh = RefreshToken.for_user(user)
        timeout_minutes = max(5, get_setting_int('session_timeout_minutes', 30))
        expires_at = timezone.now() + timedelta(days=7)
        session = Session.objects.create(
            user=user,
            refresh_token_jti=refresh['jti'],
            expires_at=expires_at,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user_uuid': str(user.uuid),
            'session_uuid': str(session.uuid),
            'session_timeout_minutes': timeout_minutes,
        }

    @staticmethod
    def revoke_session(refresh_token_jti):
        """Revoke a session by refresh token JTI (used for logout)."""
        try:
            session = Session.objects.get(refresh_token_jti=refresh_token_jti)
            session.is_active = False
            session.revoked_at = timezone.now()
            session.save(update_fields=['is_active', 'revoked_at'])
            return True
        except Session.DoesNotExist:
            return False
