"""Re-point elections that still use frozen clone registers onto shared institutional registers."""

from django.core.management.base import BaseCommand

from elections.models import Election
from elections.services.register_service import ensure_election_uses_live_register


class Command(BaseCommand):
    help = (
        'Attach elections to the live institutional register when they still point at '
        'an election-owned clone. Keeps one register = one dynamic voter list.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without writing.',
        )

    def handle(self, *args, **options):
        dry = bool(options.get('dry_run'))
        fixed = 0
        skipped = 0

        elections = (
            Election.objects.select_related('register', 'institution', 'owner_ec_unit')
            .filter(register__isnull=False)
        )
        for election in elections.iterator():
            register = election.register
            if not register:
                skipped += 1
                continue

            before_uuid = str(register.uuid)
            before_count = register.entries.count()

            if dry:
                from elections.services.register_service import find_live_institutional_register

                institution = (
                    election.institution
                    or getattr(election.owner_ec_unit, 'institution', None)
                    or register.institution
                )
                live = find_live_institutional_register(register, institution=institution)
                if not live or live.pk == register.pk:
                    skipped += 1
                    continue
                self.stdout.write(
                    f'Election “{election.title}”: {before_uuid} ({before_count} entries) '
                    f'→ institutional {live.uuid} ({live.entries.count()} entries)'
                )
                fixed += 1
                continue

            changed = ensure_election_uses_live_register(election, sync=True)
            if not changed:
                skipped += 1
                continue
            election.refresh_from_db()
            self.stdout.write(
                f'Election “{election.title}”: {before_uuid} ({before_count} entries) '
                f'→ institutional {election.register.uuid} ({election.register.entries.count()} entries)'
            )
            fixed += 1

        self.stdout.write(self.style.SUCCESS(f'Done. fixed={fixed} skipped={skipped} dry_run={dry}'))
