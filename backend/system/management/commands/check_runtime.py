from django.conf import settings
from django.core.management.base import BaseCommand

from system.settings_utils import get_setting, get_setting_bool


class Command(BaseCommand):
    help = 'Verify Redis, Celery workers, SMS config, and USSD readiness.'

    def handle(self, *args, **options):
        ok = True

        redis_url = (getattr(settings, 'REDIS_URL', None) or '').strip()
        broker = (getattr(settings, 'CELERY_BROKER_URL', None) or '').strip()
        self.stdout.write(f'REDIS_URL: {redis_url or "(not set)"}')
        self.stdout.write(f'CELERY_BROKER_URL: {broker or "(not set)"}')

        # Redis
        try:
            import redis
            url = redis_url or broker or 'redis://127.0.0.1:6379/0'
            client = redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
            client.ping()
            self.stdout.write(self.style.SUCCESS(f'Redis OK ({url.split("@")[-1]})'))
        except Exception as exc:
            ok = False
            self.stderr.write(self.style.ERROR(f'Redis FAIL: {exc}'))

        # Celery workers
        try:
            from config.celery import app as celery_app
            inspector = celery_app.control.inspect(timeout=2.0)
            ping = inspector.ping() if inspector else None
            stats = inspector.stats() if inspector else None
            workers = list((ping or {}).keys())
            concurrency = 0
            if stats:
                for worker_stats in stats.values():
                    pool = worker_stats.get('pool') or {}
                    concurrency += int(pool.get('max-concurrency') or 0)
            if workers:
                self.stdout.write(self.style.SUCCESS(
                    f'Celery OK — {len(workers)} worker process(es), concurrency={concurrency}: {", ".join(workers)}'
                ))
                if concurrency < 6:
                    self.stdout.write(self.style.WARNING(
                        'Tip: start with CELERY_WORKER_CONCURRENCY=6 (or 7) for election load.'
                    ))
            else:
                ok = False
                self.stderr.write(self.style.ERROR(
                    'Celery FAIL — no workers answered ping. Run scripts/start-workers.sh'
                ))
        except Exception as exc:
            ok = False
            self.stderr.write(self.style.ERROR(f'Celery FAIL: {exc}'))

        # SMS
        sms_enabled = get_setting_bool('sms_enabled', True)
        arkesel = bool((get_setting('sms_arkesel_api_key') or get_setting('sms_api_key') or '').strip())
        moolre = bool((get_setting('sms_moolre_api_key') or '').strip())
        if sms_enabled and (arkesel or moolre):
            self.stdout.write(self.style.SUCCESS(
                f'SMS OK — enabled, primary={get_setting("sms_provider_primary") or "arkesel"}, '
                f'arkesel_key={"yes" if arkesel else "no"}, moolre_key={"yes" if moolre else "no"}'
            ))
        else:
            ok = False
            self.stderr.write(self.style.ERROR(
                'SMS FAIL — set sms_enabled=true and Arkesel/Moolre API keys in Settings'
            ))

        # USSD
        ussd_on = get_setting_bool('ussd_enabled', True)
        service = get_setting('ussd_service_code') or ''
        callback = get_setting('ussd_callback_url') or ''
        if ussd_on:
            self.stdout.write(self.style.SUCCESS(
                f'USSD OK — enabled, code={service or "?"}, callback={callback or "?"}'
            ))
        else:
            ok = False
            self.stderr.write(self.style.ERROR('USSD FAIL — ussd_enabled is false'))

        if getattr(settings, 'DEBUG', False):
            self.stdout.write(self.style.WARNING(
                'DEBUG=True — SMS may console-log instead of sending. Set DEBUG=0 in production.'
            ))

        if ok:
            self.stdout.write(self.style.SUCCESS('Runtime checks passed.'))
        else:
            self.stderr.write(self.style.ERROR('Runtime checks failed.'))
            raise SystemExit(1)
