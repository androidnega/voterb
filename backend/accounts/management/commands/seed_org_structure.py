from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Seed production org structure for Super Admin: TTU institution, Main EC, '
        'and faculties/departments from academic_structure.csv.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--name', default='Takoradi Technical University')
        parser.add_argument('--short-name', default='TTU')
        parser.add_argument('--code', default='TTU')
        parser.add_argument(
            '--rename',
            action='store_true',
            default=True,
            help='Rename institution to the provided name/short-name (default: on).',
        )
        parser.add_argument(
            '--no-rename',
            action='store_false',
            dest='rename',
            help='Do not force-rename an existing institution matched by code.',
        )

    def handle(self, *args, **options):
        call_command('seed_roles')
        bootstrap_kwargs = {
            'name': options['name'],
            'short_name': options['short_name'],
            'code': options['code'],
        }
        if options['rename']:
            bootstrap_kwargs['rename'] = True
        call_command('bootstrap_institution', **bootstrap_kwargs)
        call_command('seed_academic_structure')
        self.stdout.write(self.style.SUCCESS(
            'Org structure ready. Super Admin can assign Main EC users to the institution.'
        ))
