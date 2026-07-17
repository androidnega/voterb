from django.core.management.base import BaseCommand
from system.models import SystemSetting, FeatureFlag

class Command(BaseCommand):
    help = 'Seed SMS, USSD settings and feature flags'

    def handle(self, *args, **options):
        # SMS Settings
        sms_settings = [
            {'key': 'sms_provider_primary', 'value': 'arkesel', 'category': 'integrations', 'description': 'Primary SMS provider (arkesel, moolre, twilio)'},
            {'key': 'sms_provider_fallback', 'value': 'moolre', 'category': 'integrations', 'description': 'Fallback SMS provider if primary fails'},
            {'key': 'sms_arkesel_api_key', 'value': '', 'category': 'integrations', 'description': 'Arkesel API key', 'is_encrypted': True},
            {'key': 'sms_arkesel_sender_id', 'value': 'VoterB', 'category': 'integrations', 'description': 'Arkesel sender ID'},
            {'key': 'sms_arkesel_url', 'value': 'https://sms.arkesel.com/api/v2/sms/send', 'category': 'integrations', 'description': 'Arkesel SMS API URL'},
            {'key': 'sms_moolre_api_key', 'value': '', 'category': 'integrations', 'description': 'Moolre API key', 'is_encrypted': True},
            {'key': 'sms_moolre_sender_id', 'value': 'VoterB', 'category': 'integrations', 'description': 'Moolre sender ID'},
            {'key': 'sms_moolre_url', 'value': 'https://api.moolre.com/open/sms/send', 'category': 'integrations', 'description': 'Moolre SMS API URL'},
            {'key': 'sms_enabled', 'value': 'true', 'category': 'integrations', 'description': 'Enable SMS notifications'},
        ]

        # USSD Settings
        ussd_settings = [
            {'key': 'ussd_enabled', 'value': 'true', 'category': 'integrations', 'description': 'Enable USSD voting channel'},
            {'key': 'ussd_service_code', 'value': '*928*013#', 'category': 'integrations', 'description': 'USSD service code'},
            {'key': 'ussd_callback_url', 'value': 'https://votebridge.online/api/v1/ussd/callback/', 'category': 'integrations', 'description': 'USSD callback webhook URL'},
            {'key': 'ussd_session_timeout', 'value': '1800', 'category': 'integrations', 'description': 'USSD session timeout in seconds (non-SVT steps)'},
            {'key': 'ussd_svt_resume_seconds', 'value': '7200', 'category': 'integrations', 'description': 'How long an SVT wait session can be resumed after hang-up (seconds)'},
            {'key': 'ussd_retry_attempts', 'value': '3', 'category': 'integrations', 'description': 'USSD retry attempts per session'},
            {'key': 'ussd_rate_limit_per_minute', 'value': '10', 'category': 'integrations', 'description': 'Max USSD callback requests per MSISDN per minute'},
            {'key': 'ussd_api_key', 'value': '', 'category': 'integrations', 'description': 'Leave blank for Arkesel (they do not send X-API-Key on USSD callbacks)', 'is_encrypted': True},
        ]

        # Additional Settings
        other_settings = [
            {'key': 'ui_theme', 'value': 'classic', 'category': 'general', 'description': 'Platform UI color theme (classic, pulse, amber)'},
            {'key': 'ui_dashboard', 'value': 'atelier', 'category': 'general', 'description': 'Admin dashboard layout template (atelier, operations, lumen)'},
            {'key': 'email_enabled', 'value': 'true', 'category': 'integrations', 'description': 'Enable email notifications'},
            {'key': 'email_from_address', 'value': 'noreply@voterb.com', 'category': 'integrations', 'description': 'Email from address'},
            {'key': 'email_smtp_host', 'value': 'smtp.gmail.com', 'category': 'integrations', 'description': 'SMTP host'},
            {'key': 'email_smtp_port', 'value': '587', 'category': 'integrations', 'description': 'SMTP port'},
            {'key': 'email_smtp_username', 'value': '', 'category': 'integrations', 'description': 'SMTP username', 'is_encrypted': True},
            {'key': 'email_smtp_password', 'value': '', 'category': 'integrations', 'description': 'SMTP password', 'is_encrypted': True},
        ]

        # Feature Flags
        feature_flags = [
            {'key': 'ussd_voting', 'is_enabled': True, 'category': 'voting', 'description': 'Enable USSD voting channel'},
            {'key': 'web_voting', 'is_enabled': True, 'category': 'voting', 'description': 'Enable web voting channel'},
            {'key': 'biometric_auth', 'is_enabled': False, 'category': 'security', 'description': 'Enable biometric authentication for staff'},
            {'key': 'sms_notifications', 'is_enabled': True, 'category': 'notifications', 'description': 'Enable SMS notifications'},
            {'key': 'email_notifications', 'is_enabled': True, 'category': 'notifications', 'description': 'Enable email notifications'},
            {'key': 'student_registration', 'is_enabled': False, 'category': 'governance', 'description': 'Allow students to self-register'},
            {'key': 'results_auto_generate', 'is_enabled': True, 'category': 'results', 'description': 'Auto-generate results when election closes'},
            {'key': 'strongroom_enabled', 'is_enabled': True, 'category': 'security', 'description': 'Enable Strongroom integrity features'},
            {'key': 'fraud_detection', 'is_enabled': True, 'category': 'security', 'description': 'Enable automated fraud detection'},
            {'key': 'audit_logging', 'is_enabled': True, 'category': 'security', 'description': 'Enable detailed audit logging'},
            {'key': 'maintenance_mode', 'is_enabled': False, 'category': 'operations', 'description': 'Enable maintenance mode'},
        ]

        all_settings = sms_settings + ussd_settings + other_settings
        for setting in all_settings:
            obj, created = SystemSetting.objects.get_or_create(key=setting['key'])
            if created:
                obj.value = setting['value']
                obj.category = setting.get('category', 'general')
                obj.description = setting.get('description', '')
                obj.is_encrypted = setting.get('is_encrypted', False)
                obj.save()
                self.stdout.write(self.style.SUCCESS(f'Created setting: {setting["key"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Setting already exists: {setting["key"]}'))

        for flag in feature_flags:
            obj, created = FeatureFlag.objects.get_or_create(key=flag['key'])
            if created:
                obj.is_enabled = flag['is_enabled']
                obj.category = flag.get('category', 'general')
                obj.description = flag.get('description', '')
                obj.save()
                self.stdout.write(self.style.SUCCESS(f'Created feature flag: {flag["key"]}'))
            else:
                self.stdout.write(self.style.WARNING(f'Feature flag already exists: {flag["key"]}'))

        self.stdout.write(self.style.SUCCESS('✅ SMS, USSD, and feature settings seeded!'))
