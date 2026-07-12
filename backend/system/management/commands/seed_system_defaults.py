from django.core.management.base import BaseCommand
from system.models import SystemSetting, FeatureFlag, InstitutionProfile, MaintenanceState

class Command(BaseCommand):
    help = 'Seed default system settings and feature flags'

    def handle(self, *args, **options):
        profile, _ = InstitutionProfile.objects.get_or_create(
            name='VoterB',
            defaults={
                'short_name': 'VoterB',
                'primary_color': '#1e5f46',
                'secondary_color': '#0f7d3e',
                'contact_email': 'info@voterb.com'
            }
        )
        self.stdout.write(self.style.SUCCESS('Institution profile created'))

        settings = [
            {'key': 'site_name', 'value': 'VoterB', 'category': 'general', 'description': 'Site name displayed in the header'},
            {'key': 'site_tagline', 'value': 'Secure Campus Elections', 'category': 'general', 'description': 'Tagline shown on the login page'},
            {'key': 'session_timeout_minutes', 'value': '30', 'category': 'security', 'description': 'Session timeout in minutes'},
            {'key': 'max_login_attempts', 'value': '5', 'category': 'security', 'description': 'Maximum failed login attempts before lockout'},
            {'key': 'otp_length', 'value': '6', 'category': 'security', 'description': 'Digit count after the rte- prefix (e.g. rte-123456)'},
            {'key': 'otp_expiry_minutes', 'value': '5', 'category': 'security', 'description': 'OTP expiry time in minutes'},
            {'key': 'svt_expiry_minutes', 'value': '10', 'category': 'security', 'description': 'SVT expiry time in minutes'},
            {'key': 'svt_max_requests_per_hour', 'value': '5', 'category': 'security', 'description': 'Max SVT request/resend actions per voter per election per hour'},
            {'key': 'svt_resend_cooldown_seconds', 'value': '60', 'category': 'security', 'description': 'Minimum seconds between SVT resend requests'},
            {'key': 'svt_max_validation_attempts', 'value': '5', 'category': 'security', 'description': 'Max failed SVT validation attempts before the token is revoked'},
            {'key': 'allow_student_registration', 'value': 'true', 'category': 'governance', 'description': 'Allow students to self-register'},
            {'key': 'allow_ussd_voting', 'value': 'false', 'category': 'operations', 'description': 'Enable USSD voting channel'},
            {'key': 'allow_biometric_auth', 'value': 'false', 'category': 'operations', 'description': 'Enable biometric authentication'},
            {'key': 'sms_provider', 'value': 'arkesel', 'category': 'integrations', 'description': 'SMS provider (arkesel, twilio, moolre)'},
            {'key': 'sms_api_key', 'value': '', 'category': 'integrations', 'description': 'SMS API key'},
            {'key': 'sms_sender_id', 'value': 'VoterB', 'category': 'integrations', 'description': 'SMS sender ID'},
            {'key': 'email_from_address', 'value': 'noreply@voterb.com', 'category': 'integrations', 'description': 'Email from address'},
        ]
        
        for setting in settings:
            obj, created = SystemSetting.objects.get_or_create(key=setting['key'])
            if created:
                obj.value = setting['value']
                obj.category = setting['category']
                obj.description = setting['description']
                obj.save()

        flags = [
            {'key': 'ussd_voting', 'is_enabled': False, 'description': 'Enable USSD voting channel'},
            {'key': 'biometric_auth', 'is_enabled': False, 'description': 'Enable biometric authentication for staff'},
            {'key': 'student_registration', 'is_enabled': True, 'description': 'Allow students to register themselves'},
            {'key': 'email_notifications', 'is_enabled': True, 'description': 'Send email notifications'},
            {'key': 'sms_notifications', 'is_enabled': True, 'description': 'Send SMS notifications'},
            {'key': 'results_auto_generate', 'is_enabled': True, 'description': 'Auto-generate results when election closes'},
            {'key': 'strongroom_enabled', 'is_enabled': True, 'description': 'Enable Strongroom integrity features'},
        ]
        
        for flag in flags:
            obj, created = FeatureFlag.objects.get_or_create(key=flag['key'])
            if created:
                obj.is_enabled = flag['is_enabled']
                obj.description = flag['description']
                obj.save()

        MaintenanceState.objects.get_or_create(
            is_active=False,
            defaults={'message': 'The system is currently under maintenance. Please check back later.'}
        )
        self.stdout.write(self.style.SUCCESS('✅ System defaults seeded!'))
