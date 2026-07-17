from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Deprecated: candidates no longer store faculty/department fields. '
        'This command is a no-op retained for compatibility.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--election-title', default='TTU SRC Elections 2026')
        parser.add_argument('--all-elections', action='store_true')

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'Candidate academic refs were removed. Nothing to sync.'
        ))
