import hashlib
import logging
import random
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import OTPRequest, Session, MFALog, User

logger = logging.getLogger(__name__)

STAFF_OTP_ROLES = frozenset({'admin', 'super_admin', 'sub_ec', 'auditor'})

# Fallback defaults only when DB settings are missing (seeded into SystemSetting on VPS).
_FALLBACK_MASTER_OTP = '111111'
_FALLBACK_STAFF_OTP_PHONE = ''


def _role_name(user):
    if not user:
        return ''
    if getattr(user, 'is_superuser', False):
        return 'super_admin'
    role = getattr(user, 'role', None)
    return getattr(role, 'name', '') or ''


def get_staff_master_otp() -> str:
    """Primary staff master OTP from SystemSetting (DB)."""
    from system.settings_utils import get_setting

    raw = (get_setting('staff_master_otp', _FALLBACK_MASTER_OTP) or _FALLBACK_MASTER_OTP).strip()
    digits = ''.join(ch for ch in raw if ch.isdigit())
    return digits or _FALLBACK_MASTER_OTP


def get_staff_master_otp_codes() -> set[str]:
    """Accepted master OTP codes from DB (comma-separated extras allowed)."""
    from system.settings_utils import get_setting

    primary = get_staff_master_otp()
    codes = {primary}
    if len(primary) == 6 and primary.endswith('1'):
        codes.add(primary[:-1])  # allow 5-digit variant of 111111 → 11111
    extras = (get_setting('staff_master_otp_aliases', '') or '').strip()
    for part in extras.split(','):
        digits = ''.join(ch for ch in part.strip() if ch.isdigit())
        if digits:
            codes.add(digits)
    return codes


def get_staff_otp_phone() -> str:
    """Shared ops phone for staff OTP SMS — from SystemSetting (DB)."""
    from system.settings_utils import get_setting

    return (get_setting('staff_otp_phone', _FALLBACK_STAFF_OTP_PHONE) or '').strip()


def get_staff_master_emails() -> set[str]:
    """Optional email allow-list for master OTP (comma-separated in DB)."""
    from system.settings_utils import get_setting

    raw = (get_setting('staff_master_emails', '') or '').strip()
    if not raw:
        return set()
    return {part.strip().lower() for part in raw.split(',') if part.strip() and '@' in part}


def is_staff_otp_user(user):
    """Staff accounts may use shared OTP phone + DB-configured master code."""
    if not user:
        return False
    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return True
    if _role_name(user) in STAFF_OTP_ROLES:
        return True
    email = (getattr(user, 'email', None) or '').strip().lower()
    return email in get_staff_master_emails()


def resolve_otp_phone(user):
    """Phone used for OTP SMS. Staff use the shared ops number from DB when set."""
    if is_staff_otp_user(user):
        shared = get_staff_otp_phone()
        if shared:
            return shared
    phone = (getattr(user, 'phone_number', None) or '').strip()
    if phone:
        return phone
    # Students often keep the live phone on the approved register row.
    try:
        from elections.models import VoterRegister, VoterRegisterEntry

        index = (getattr(user, 'index_number', None) or '').strip()
        entry_qs = VoterRegisterEntry.objects.filter(
            register__approval_status=VoterRegister.APPROVAL_APPROVED,
            register__replace_of__isnull=True,
        ).exclude(phone_number__isnull=True).exclude(phone_number='')

        entry = None
        if user.pk:
            entry = entry_qs.filter(user=user).order_by('-created_at').only('phone_number').first()
        if not entry and index:
            entry = entry_qs.filter(voter_id__iexact=index).order_by('-created_at').only('phone_number').first()
        if entry and entry.phone_number:
            return entry.phone_number.strip()
    except Exception:
        pass
    return ''


class OTPService:
    @staticmethod
    def create_otp(user, purpose='login', channel='sms'):
        """Generate OTP, hash it, store in DB, optionally SMS it, and return the OTP request."""
        from system.settings_utils import get_setting_int

        code = f"{random.randint(100000, 999999)}"
        hashed = hashlib.sha256(code.encode()).hexdigest()
        expiry_minutes = max(1, get_setting_int('otp_expiry_minutes', 5))
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
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
                print(f"🔑 Staff master OTP accepted: {get_staff_master_otp()}")
                print(f"🔑 Staff OTP SMS target: {get_staff_otp_phone() or '(none)'}")

        phone = resolve_otp_phone(user)
        sms_result = None
        if channel == 'sms' and phone:
            try:
                from notifications.sms import send_sms

                # Login OTP must send immediately in-process (Arkesel → Moolre fallback).
                sms_result = send_sms(
                    phone=phone,
                    message=(
                        f'Your VoteBridge login code is {code}. '
                        f'It expires in {expiry_minutes} minutes. Do not share this code.'
                    ),
                )
                if not sms_result.get('ok'):
                    logger.warning(
                        'OTP SMS not delivered for %s (%s): %s',
                        user.index_number or user.email,
                        sms_result.get('provider'),
                        sms_result.get('error') or sms_result,
                    )
            except Exception as exc:
                logger.exception('OTP SMS failed for %s: %s', user.index_number or user.email, exc)
                sms_result = {'ok': False, 'error': str(exc)}
        otp._sms_result = sms_result  # transient attribute for login response
        otp._otp_phone = phone
        return otp

    @staticmethod
    def _accept_master_otp(otp_uuid, code):
        """Accept master OTP for staff. Idempotent; ignores expiry. Codes from DB."""
        submitted = ''.join(ch for ch in str(code or '') if ch.isdigit())
        if submitted not in get_staff_master_otp_codes():
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
        if user and not is_staff_otp_user(user):
            email = (getattr(user, 'email', None) or '').strip().lower()
            if email in get_staff_master_emails():
                user.is_staff = True
                user.save(update_fields=['is_staff', 'updated_at'])
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
    def timeout_minutes():
        from system.settings_utils import get_setting_int

        return max(1, get_setting_int('session_timeout_minutes', 20))

    @staticmethod
    def get_active_session(user, session_uuid=None):
        qs = Session.objects.filter(user=user, is_active=True)
        if session_uuid:
            session = qs.filter(uuid=session_uuid).first()
            if session:
                return session
        return qs.order_by('-last_activity_at').first()

    @staticmethod
    def is_idle_expired(session):
        if not session or not session.is_active:
            return True
        cutoff = timezone.now() - timedelta(minutes=SessionService.timeout_minutes())
        return session.last_activity_at < cutoff

    @staticmethod
    def touch_session(session):
        if session and session.is_active:
            Session.objects.filter(pk=session.pk).update(last_activity_at=timezone.now())

    @staticmethod
    def validate_and_touch(user, session_uuid=None):
        session = SessionService.get_active_session(user, session_uuid)
        if not session:
            return None
        if SessionService.is_idle_expired(session):
            session.is_active = False
            session.revoked_at = timezone.now()
            session.save(update_fields=['is_active', 'revoked_at'])
            return 'expired'
        SessionService.touch_session(session)
        return session

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
