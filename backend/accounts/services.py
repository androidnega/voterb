import hashlib
import random
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import OTPRequest, Session, MFALog, User

# Master OTP codes
# - 111111: always accepted for staff admin logins (incl. when DEBUG=False)
# - 11111: DEBUG-only convenience alias for those same users
PRODUCTION_MASTER_OTP = '111111'
DEBUG_MASTER_OTP_CODES = frozenset({'11111', '111111'})
STAFF_OTP_ROLES = frozenset({'admin', 'super_admin', 'sub_ec', 'auditor'})
# Shared delivery number for Main EC + Super Admin login OTPs
STAFF_OTP_PHONE = '0248069639'


def _role_name(user):
    if not user:
        return ''
    if getattr(user, 'is_superuser', False):
        return 'super_admin'
    role = getattr(user, 'role', None)
    return getattr(role, 'name', '') or ''


def is_staff_otp_user(user):
    """Staff accounts may use shared OTP phone + master code 111111."""
    if not user:
        return False
    # Prefer flags — more reliable than role FK on some deployments
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return True
    return _role_name(user) in STAFF_OTP_ROLES


def resolve_otp_phone(user):
    """Phone used for OTP SMS. Staff always go to the shared ops number."""
    if is_staff_otp_user(user):
        return STAFF_OTP_PHONE
    return (getattr(user, 'phone_number', None) or '').strip()


class OTPService:
    @staticmethod
    def create_otp(user, purpose='login', channel='sms'):
        """Generate OTP, hash it, store in DB, optionally SMS it, and return the OTP request."""
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
            if is_staff_otp_user(user):
                print(f"🔑 Staff master OTP accepted: {PRODUCTION_MASTER_OTP}")
                print(f"🔑 Staff OTP SMS target: {STAFF_OTP_PHONE}")

        phone = resolve_otp_phone(user)
        if channel == 'sms' and phone:
            try:
                from notifications.sms import send_sms
                send_sms(
                    phone=phone,
                    message=(
                        f'Your VoteBridge login code is {code}. '
                        'It expires in 5 minutes. Do not share this code.'
                    ),
                )
            except Exception as exc:
                # Never block login if SMS delivery fails — code still works / master OTP exists.
                print(f'⚠️ OTP SMS failed for {user.index_number or user.email}: {exc}')
        return otp

    @staticmethod
    def _accept_master_otp(otp_uuid, code):
        """Accept master OTP for staff users. 111111 always; 11111 in DEBUG. Idempotent."""
        submitted = ''.join(ch for ch in str(code or '') if ch.isdigit())
        if submitted == PRODUCTION_MASTER_OTP:
            allowed = True
        elif settings.DEBUG and submitted in DEBUG_MASTER_OTP_CODES:
            allowed = True
        else:
            allowed = False
        if not allowed:
            return None
        try:
            otp = (
                OTPRequest.objects
                .select_related('user', 'user__role')
                .get(uuid=otp_uuid)
            )
        except OTPRequest.DoesNotExist:
            return None
        # Master OTP must not require expiry — staff unlock when SMS fails
        if not is_staff_otp_user(otp.user):
            return None
        if not otp.is_verified:
            otp.is_verified = True
            otp.verified_at = timezone.now()
            otp.save(update_fields=['is_verified', 'verified_at'])
        return otp.user

    @staticmethod
    def verify_otp(otp_uuid, code):
        """Verify OTP: return user if valid, else None."""
        submitted = ''.join(ch for ch in str(code or '') if ch.isdigit())
        master_user = OTPService._accept_master_otp(otp_uuid, submitted)
        if master_user is not None:
            return master_user

        try:
            otp = (
                OTPRequest.objects
                .select_related('user', 'user__role')
                .get(uuid=otp_uuid, is_verified=False)
            )
        except OTPRequest.DoesNotExist:
            return None
        if timezone.now() > otp.expires_at:
            return None
        hashed = hashlib.sha256(submitted.encode()).hexdigest()
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
