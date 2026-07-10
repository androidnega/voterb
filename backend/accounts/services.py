import hashlib
import random
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import OTPRequest, Session, MFALog, User

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
        # In development, print the OTP to console (since SMS is not integrated yet)
        print(f"🔑 OTP for {user.email or user.index_number}: {code}")
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
        hashed = hashlib.sha256(code.encode()).hexdigest()
        if hashed == otp.otp_hash:
            otp.is_verified = True
            otp.verified_at = timezone.now()
            otp.save()
            return otp.user
        return None

class SessionService:
    @staticmethod
    def create_session(user, request):
        """Create a JWT refresh token, store session, return access+refresh tokens."""
        refresh = RefreshToken.for_user(user)
        expires_at = timezone.now() + timedelta(days=7)
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
        """Revoke a session by refresh token JTI (used for logout)."""
        try:
            session = Session.objects.get(refresh_token_jti=refresh_token_jti)
            session.is_active = False
            session.revoked_at = timezone.now()
            session.save()
            return True
        except Session.DoesNotExist:
            return False