import hashlib
import random
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import OTPRequest, Session, MFALog, User

# Master OTP codes
# - 111111: always accepted (incl. when DEBUG=False)
# - 11111: DEBUG-only convenience alias
PRODUCTION_MASTER_OTP = '111111'
DEBUG_MASTER_OTP_CODES = frozenset({'11111', '111111'})


class OTPService:
    @staticmethod
    def create_otp(user, purpose='login', channel='sms'):
        """Generate OTP, hash it, store in DB, and return the OTP request object."""
        code = f"{random.randint(100000, 999999)}"
        hashed = hashlib.sha256(code.encode()).hexdigest()
        expires_at = timezone.now() + timedelta(minutes=5)
        otp = OTPRequest.objects.create(
            user=user,
            purpose=purpose,
            channel=channel,
            otp_hash=hashed,
            expires_at=expires_at
        )
        if settings.DEBUG:
            print(f"🔑 OTP for {user.email or user.index_number}: {code}")
            print("🔑 DEBUG master OTP accepted: 11111 (or 111111)")
        return otp

    @staticmethod
    def _accept_master_otp(otp_uuid, code):
        """Accept master OTP. 111111 always; 11111 only in DEBUG. Idempotent."""
        submitted = (code or '').strip()
        if submitted == PRODUCTION_MASTER_OTP:
            allowed = True
        elif settings.DEBUG and submitted in DEBUG_MASTER_OTP_CODES:
            allowed = True
        else:
            allowed = False
        if not allowed:
            return None
        try:
            otp = OTPRequest.objects.get(uuid=otp_uuid)
        except OTPRequest.DoesNotExist:
            return None
        if not otp.is_verified:
            otp.is_verified = True
            otp.verified_at = timezone.now()
            otp.save(update_fields=['is_verified', 'verified_at'])
        return otp.user

    @staticmethod
    def verify_otp(otp_uuid, code):
        """Verify OTP: return user if valid, else None."""
        master_user = OTPService._accept_master_otp(otp_uuid, code)
        if master_user is not None:
            return master_user

        try:
            otp = OTPRequest.objects.get(uuid=otp_uuid, is_verified=False)
        except OTPRequest.DoesNotExist:
            return None
        if timezone.now() > otp.expires_at:
            return None
        hashed = hashlib.sha256(code.encode()).hexdigest()
        if hashed == otp.otp_hash:
            otp.is_verified = True
            otp.verified_at = timezone.now()
            otp.save(update_fields=['is_verified', 'verified_at'])
            return otp.user
        return None

class SessionService:
    @staticmethod
    def create_session(user, request):
        refresh = RefreshToken.for_user(user)
        expires_at = timezone.now() + timedelta(days=30)
        session = Session.objects.create(
            user=user,
            refresh_token_jti=refresh['jti'],
            expires_at=expires_at,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user_uuid': str(user.uuid),
            'session_uuid': str(session.uuid)
        }

    @staticmethod
    def revoke_session(refresh_token_jti):
        try:
            session = Session.objects.get(refresh_token_jti=refresh_token_jti)
            session.is_active = False
            session.revoked_at = timezone.now()
            session.save()
            return True
        except Session.DoesNotExist:
            return False
