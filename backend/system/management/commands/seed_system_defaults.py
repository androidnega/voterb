from django.core.management.base import BaseCommand

from system.models import SystemSetting, FeatureFlag, InstitutionProfile, MaintenanceState


class Command(BaseCommand):
    help = 'Seed default system settings, integrations (SMS/USSD), and feature flags'

    def handle(self, *args, **options):
        profile = InstitutionProfile.objects.order_by('created_at', 'name').first()
        if not profile:
            profile = InstitutionProfile.objects.create(
                name='Takoradi Technical University',
                short_name='TTU',
                code='TTU',
                primary_color='#1e5f46',
                secondary_color='#0f7d3e',
                contact_email='info@votebridge.online',
            )
            self.stdout.write(self.style.SUCCESS(f'Institution profile created: {profile.name}'))
        else:
            self.stdout.write(f'Using institution: {profile.name}')

        settings = [
            # General / appearance
            {'key': 'site_name', 'value': 'VoteBridge', 'category': 'general', 'description': 'Site name displayed in the header'},
            {'key': 'site_tagline', 'value': 'Secure Campus Elections', 'category': 'general', 'description': 'Tagline shown on the login page'},
            {'key': 'ui_theme', 'value': 'classic', 'category': 'general', 'description': 'Platform UI color theme (classic, pulse, amber)'},
            {'key': 'ui_dashboard', 'value': 'atelier', 'category': 'general', 'description': 'Admin dashboard layout template'},

            # Security
            {'key': 'session_timeout_minutes', 'value': '30', 'category': 'security', 'description': 'Session timeout in minutes'},
            {'key': 'max_login_attempts', 'value': '5', 'category': 'security', 'description': 'Maximum failed login attempts before lockout'},
            {'key': 'otp_length', 'value': '6', 'category': 'security', 'description': 'Number of digits in the login OTP'},
            {'key': 'otp_expiry_minutes', 'value': '5', 'category': 'security', 'description': 'OTP expiry time in minutes'},
            {'key': 'svt_expiry_minutes', 'value': '20', 'category': 'security', 'description': 'SVT lifetime in minutes after issue'},
            {'key': 'svt_max_requests_total', 'value': '3', 'category': 'security', 'description': 'Max SVT requests per voter per election'},
            {'key': 'svt_max_requests_per_hour', 'value': '3', 'category': 'security', 'description': 'Legacy SVT hourly limit'},
            {'key': 'svt_resend_cooldown_seconds', 'value': '60', 'category': 'security', 'description': 'Minimum seconds between SVT resend requests'},
            {'key': 'svt_max_validation_attempts', 'value': '5', 'category': 'security', 'description': 'Max failed SVT validation attempts'},
            {'key': 'svt_cross_user_block_minutes', 'value': '60', 'category': 'security', 'description': 'Lockout when a voter tries another voter live SVT'},

            # SMS — Arkesel / Moolre
            {'key': 'sms_enabled', 'value': 'true', 'category': 'integrations', 'description': 'Enable SMS notifications'},
            {'key': 'sms_provider_primary', 'value': 'arkesel', 'category': 'integrations', 'description': 'Primary SMS provider (arkesel, moolre, twilio)'},
            {'key': 'sms_provider_fallback', 'value': 'moolre', 'category': 'integrations', 'description': 'Fallback SMS provider if primary fails'},
            {'key': 'sms_arkesel_api_key', 'value': '', 'category': 'integrations', 'description': 'Arkesel API key', 'is_encrypted': True},
            {'key': 'sms_arkesel_sender_id', 'value': 'VoteBridge', 'category': 'integrations', 'description': 'Arkesel sender ID'},
            {'key': 'sms_arkesel_url', 'value': 'https://sms.arkesel.com/api/v2/sms/send', 'category': 'integrations', 'description': 'Arkesel SMS API URL'},
            {'key': 'sms_moolre_api_key', 'value': '', 'category': 'integrations', 'description': 'Moolre API key', 'is_encrypted': True},
            {'key': 'sms_moolre_sender_id', 'value': 'VoteBridge', 'category': 'integrations', 'description': 'Moolre sender ID'},
            {'key': 'sms_moolre_url', 'value': 'https://api.moolre.com/v1/sms/send', 'category': 'integrations', 'description': 'Moolre SMS API URL'},
            {'key': 'sms_api_key', 'value': '', 'category': 'integrations', 'description': 'Legacy SMS API key alias', 'is_encrypted': True},
            {'key': 'sms_sender_id', 'value': 'VoteBridge', 'category': 'integrations', 'description': 'Legacy SMS sender ID'},

            # USSD / Arkesel USSD gateway
            {'key': 'ussd_enabled', 'value': 'true', 'category': 'integrations', 'description': 'Enable USSD voting channel'},
            {'key': 'ussd_service_code', 'value': '*928*013#', 'category': 'integrations', 'description': 'USSD service code'},
            {'key': 'ussd_callback_url', 'value': 'https://votebridge.online/api/v1/ussd/callback/', 'category': 'integrations', 'description': 'USSD callback webhook URL for Arkesel'},
            {'key': 'ussd_session_timeout', 'value': '1800', 'category': 'integrations', 'description': 'USSD session timeout in seconds'},
            {'key': 'ussd_svt_resume_seconds', 'value': '7200', 'category': 'integrations', 'description': 'How long an SVT wait session can be resumed'},
            {'key': 'ussd_retry_attempts', 'value': '3', 'category': 'integrations', 'description': 'USSD retry attempts per session'},
            {'key': 'ussd_rate_limit_per_minute', 'value': '10', 'category': 'integrations', 'description': 'Max USSD callback requests per MSISDN per minute'},
            {'key': 'ussd_api_key', 'value': '', 'category': 'integrations', 'description': 'Optional USSD webhook API key (X-API-Key)', 'is_encrypted': True},

            # Email
            {'key': 'email_enabled', 'value': 'true', 'category': 'integrations', 'description': 'Enable email notifications'},
            {'key': 'email_from_address', 'value': 'noreply@votebridge.online', 'category': 'integrations', 'description': 'Email from address'},
            {'key': 'email_smtp_host', 'value': 'smtp.gmail.com', 'category': 'integrations', 'description': 'SMTP host'},
            {'key': 'email_smtp_port', 'value': '587', 'category': 'integrations', 'description': 'SMTP port'},
            {'key': 'email_smtp_username', 'value': '', 'category': 'integrations', 'description': 'SMTP username', 'is_encrypted': True},
            {'key': 'email_smtp_password', 'value': '', 'category': 'integrations', 'description': 'SMTP password', 'is_encrypted': True},

            # Governance / ops toggles (mirrored by feature flags where applicable)
            {'key': 'allow_student_registration', 'value': 'false', 'category': 'governance', 'description': 'Allow students to self-register'},
            {'key': 'allow_ussd_voting', 'value': 'true', 'category': 'operations', 'description': 'Enable USSD voting channel'},
            {'key': 'allow_biometric_auth', 'value': 'false', 'category': 'operations', 'description': 'Enable biometric authentication'},
        ]

        for setting in settings:
            obj, created = SystemSetting.objects.get_or_create(key=setting['key'])
            if created:
                obj.value = setting['value']
                obj.category = setting['category']
                obj.description = setting['description']
                obj.is_encrypted = setting.get('is_encrypted', False)
                obj.save()
                self.stdout.write(self.style.SUCCESS(f'Created setting: {setting["key"]}'))
            else:
                # Keep live secrets/values, but refresh category/description metadata
                changed = False
                if not obj.category:
                    obj.category = setting['category']
                    changed = True
                if not obj.description and setting.get('description'):
                    obj.description = setting['description']
                    changed = True
                if setting.get('is_encrypted') and not obj.is_encrypted:
                    obj.is_encrypted = True
                    changed = True
                # Fill empty callback / service code with live defaults
                if setting['key'] in ('ussd_callback_url', 'ussd_service_code') and not (obj.value or '').strip():
                    obj.value = setting['value']
                    changed = True
                if changed:
                    obj.save()
                    self.stdout.write(self.style.WARNING(f'Updated metadata: {setting["key"]}'))
                else:
                    self.stdout.write(f'Exists: {setting["key"]}')

        flags = [
            {'key': 'ussd_voting', 'is_enabled': True, 'category': 'voting', 'description': 'Enable USSD voting channel'},
            {'key': 'web_voting', 'is_enabled': True, 'category': 'voting', 'description': 'Enable web voting channel'},
            {'key': 'biometric_auth', 'is_enabled': False, 'category': 'security', 'description': 'Enable biometric authentication for staff'},
            {'key': 'sms_notifications', 'is_enabled': True, 'category': 'notifications', 'description': 'Send SMS notifications'},
            {'key': 'email_notifications', 'is_enabled': True, 'category': 'notifications', 'description': 'Send email notifications'},
            {'key': 'student_registration', 'is_enabled': False, 'category': 'governance', 'description': 'Allow students to self-register'},
            {'key': 'results_auto_generate', 'is_enabled': True, 'category': 'results', 'description': 'Auto-generate results when election closes'},
            {'key': 'strongroom_enabled', 'is_enabled': True, 'category': 'security', 'description': 'Enable Strongroom integrity features'},
            {'key': 'fraud_detection', 'is_enabled': True, 'category': 'security', 'description': 'Enable automated fraud detection'},
            {'key': 'audit_logging', 'is_enabled': True, 'category': 'security', 'description': 'Enable detailed audit logging'},
            {'key': 'maintenance_mode', 'is_enabled': False, 'category': 'operations', 'description': 'Enable maintenance mode'},
        ]

        for flag in flags:
            obj, created = FeatureFlag.objects.get_or_create(key=flag['key'])
            if created:
                obj.is_enabled = flag['is_enabled']
                obj.description = flag['description']
                obj.category = flag.get('category', 'general')
                obj.save()
                self.stdout.write(self.style.SUCCESS(f'Created flag: {flag["key"]}'))
            else:
                if not obj.description and flag.get('description'):
                    obj.description = flag['description']
                    obj.category = flag.get('category', obj.category or 'general')
                    obj.save(update_fields=['description', 'category', 'updated_at'])
                self.stdout.write(f'Exists: flag {flag["key"]}')

        if not MaintenanceState.objects.exists():
            MaintenanceState.objects.create(
                is_active=False,
                message='The system is currently under maintenance. Please check back later.',
            )
        self.stdout.write(self.style.SUCCESS('System defaults + integrations seeded.'))
