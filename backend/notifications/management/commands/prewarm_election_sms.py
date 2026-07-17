"""Pre-warm Redis SMS templates for elections opening soon (bulk-ready)."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from elections.models import Election
from notifications.sms import prewarm_election_sms_payloads


class Command(BaseCommand):
    help = (
        'Cache SVT SMS templates in Redis for elections opening within N hours '
        '(default 5). Run via cron every 15–30 minutes before large ballots.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=float,
            default=5.0,
            help='Pre-warm elections whose start_date is within this many hours (default 5).',
        )
        parser.add_argument(
            '--election',
            type=str,
            default='',
            help='Optional election UUID to pre-warm explicitly.',
        )
        parser.add_argument(
            '--include-open',
            action='store_true',
            help='Also pre-warm currently open elections.',
        )

    def handle(self, *args, **options):
        hours = max(0.5, float(options['hours'] or 5))
        now = timezone.now()
        window_end = now + timedelta(hours=hours)
        election_uuid = (options.get('election') or '').strip()

        qs = Election.objects.all()
        if election_uuid:
            qs = qs.filter(uuid=election_uuid)
        else:
            statuses = ['scheduled', 'draft']
            if options.get('include_open'):
                statuses.append('open')
            qs = qs.filter(
                status__in=statuses,
                start_date__lte=window_end,
                start_date__gte=now - timedelta(hours=1),
            )

        total_queued = 0
        total_skipped = 0
        count = 0
        for election in qs.iterator():
            result = prewarm_election_sms_payloads(election, hours_ahead=hours)
            count += 1
            total_queued += int(result.get('queued') or 0)
            total_skipped += int(result.get('skipped') or 0)
            self.stdout.write(
                self.style.SUCCESS(
                    f'{election.title}: queued={result.get("queued")} skipped={result.get("skipped")} '
                    f'ttl={result.get("ttl_seconds")}s'
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. elections={count} queued={total_queued} skipped={total_skipped} window={hours}h'
            )
        )
