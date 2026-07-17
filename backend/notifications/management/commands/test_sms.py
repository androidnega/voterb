from django.core.management.base import BaseCommand

from notifications.sms import mask_phone, normalize_msisdn, send_sms
from system.settings_utils import get_setting


class Command(BaseCommand):
    help = 'Send a test SMS through Arkesel/Moolre and print provider diagnostics.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            required=True,
            help='Recipient phone (e.g. 0248069639 or 233248069639)',
        )
        parser.add_argument(
            '--message',
            default='VoteBridge SMS test — ignore if received.',
            help='Optional test message body',
        )

    def handle(self, *args, **options):
        phone = options['phone']
        message = options['message']
        msisdn = normalize_msisdn(phone)

        self.stdout.write(f'phone: {phone}')
        self.stdout.write(f'msisdn: {msisdn or "(invalid)"}')
        self.stdout.write(f'moolre_url: {get_setting("sms_moolre_url")}')
        self.stdout.write(f'primary: {get_setting("sms_provider_primary")}')
        self.stdout.write(f'fallback: {get_setting("sms_provider_fallback")}')
        self.stdout.write(f'arkesel_sender: {get_setting("sms_arkesel_sender_id")}')
        self.stdout.write(f'moolre_sender: {get_setting("sms_moolre_sender_id")}')

        if not msisdn:
            self.stderr.write(self.style.ERROR('Invalid phone number.'))
            raise SystemExit(1)

        result = send_sms(phone=phone, message=message)
        self.stdout.write(f'masked: {result.get("masked_phone") or mask_phone(phone)}')
        self.stdout.write(f'ok: {result.get("ok")}')
        self.stdout.write(f'provider: {result.get("provider")}')
        if result.get('fallback_used'):
            self.stdout.write('fallback_used: True')
        if result.get('error'):
            self.stdout.write(self.style.ERROR(f'error: {result.get("error")}'))
        if result.get('response'):
            self.stdout.write(f'response: {result.get("response")}')

        if result.get('ok'):
            self.stdout.write(self.style.SUCCESS('Test SMS accepted by provider.'))
        else:
            self.stderr.write(self.style.ERROR('Test SMS failed.'))
            raise SystemExit(1)
