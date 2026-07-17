from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from elections.models import Election
from ussd.services.ussd_auth import issue_pin


class Command(BaseCommand):
    help = 'Issue or rotate a 6-digit USSD election PIN for a voter'

    def add_arguments(self, parser):
        parser.add_argument('--election', required=True, help='Election UUID')
        parser.add_argument('--user', required=True, help='User UUID, email, or index number')
        parser.add_argument('--pin', default='', help='Optional 6-digit PIN (generated if omitted)')

    def handle(self, *args, **options):
        election = Election.objects.filter(uuid=options['election']).first()
        if not election:
            raise CommandError('Election not found')

        ident = options['user']
        user = (
            User.objects.filter(email__iexact=ident).first()
            or User.objects.filter(index_number__iexact=ident).first()
        )
        if user is None:
            try:
                user = User.objects.filter(uuid=ident).first()
            except (ValueError, ValidationError, TypeError):
                user = None
        if not user:
            raise CommandError('User not found')

        raw = options['pin'].strip() or None
        try:
            _, pin = issue_pin(user, election, raw)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        if not election.allow_ussd_voting:
            self.stdout.write(self.style.WARNING('Election does not have allow_ussd_voting=True'))
        if election.status != 'open':
            self.stdout.write(self.style.WARNING(f'Election status is "{election.status}" (need open)'))

        self.stdout.write(self.style.SUCCESS(
            f'USSD PIN for {user} on "{election.title}": {pin}'
        ))
