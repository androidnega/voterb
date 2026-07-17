"""Ensure a staff (Main EC / Super Admin) account exists — does not touch settings or .env."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from accounts.models import ECMembership, Role, User
from accounts.org import get_or_create_main_ec_unit
from system.models import InstitutionProfile


class Command(BaseCommand):
    help = (
        'Create or update a staff login account by email. '
        'Safe for production: does not modify .env or Django settings.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--email', required=True, help='Login email')
        parser.add_argument('--password', required=True, help='Login password')
        parser.add_argument('--role', default='admin', choices=['admin', 'super_admin', 'sub_ec', 'auditor'])
        parser.add_argument('--first-name', default='')
        parser.add_argument('--last-name', default='')
        parser.add_argument(
            '--institution-code',
            default='',
            help='Institution code/short name (e.g. TTU). Required for Main EC linking.',
        )

    def _list_institutions(self):
        rows = list(
            InstitutionProfile.objects.order_by('name').values_list('code', 'short_name', 'name')[:30]
        )
        if not rows:
            return '  (none — run: python manage.py bootstrap_institution --code TTU)'
        lines = []
        for code, short_name, name in rows:
            lines.append(f'  code={code or "(empty)"}  short={short_name or "-"}  name={name}')
        return '\n'.join(lines)

    def _resolve_institution(self, raw: str):
        key = (raw or '').strip()
        if not key:
            return None
        return (
            InstitutionProfile.objects.filter(
                Q(code__iexact=key) | Q(short_name__iexact=key) | Q(name__iexact=key)
            ).first()
        )

    @transaction.atomic
    def handle(self, *args, **options):
        email = (options['email'] or '').strip().lower()
        password = options['password']
        role_name = options['role']
        if not email or '@' not in email:
            raise CommandError('Provide a valid --email')
        if len(password) < 8:
            raise CommandError('Password must be at least 8 characters')
        if password in {'YOUR_PASSWORD_HERE', 'password', 'Password1', 'changeme'}:
            raise CommandError('Choose a real password (not the placeholder).')

        institution = None
        code = (options['institution_code'] or '').strip()
        if code:
            institution = self._resolve_institution(code)
            if not institution:
                raise CommandError(
                    f'Institution {code!r} not found.\n'
                    f'Existing institutions:\n{self._list_institutions()}\n'
                    f'Create one with: python manage.py bootstrap_institution --code TTU'
                )

        role, _ = Role.objects.get_or_create(
            name=role_name,
            defaults={'description': role_name.replace('_', ' ').title()},
        )

        user = User.objects.filter(email__iexact=email).first()
        created = False
        if not user:
            user = User(
                email=email,
                first_name=(options['first_name'] or '').strip() or 'EC',
                last_name=(options['last_name'] or '').strip() or 'Member',
                role=role,
                is_staff=True,
                is_superuser=(role_name == 'super_admin'),
                is_active=True,
                is_verified=True,
                onboarding_completed=True,
            )
            user.set_password(password)
            user.save()
            created = True
            self.stdout.write(self.style.SUCCESS(f'Created user {email} ({role_name})'))
        else:
            user.role = role
            user.is_staff = True
            user.is_superuser = role_name == 'super_admin'
            user.is_active = True
            user.is_verified = True
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.WARNING(f'Updated existing user {email} ({role_name})'))

        if institution and role_name == 'admin':
            user.institution = institution
            user.save(update_fields=['institution', 'updated_at'])
            main_unit = get_or_create_main_ec_unit(institution)
            ECMembership.objects.get_or_create(
                user=user,
                ec_unit=main_unit,
                defaults={'is_active': True},
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'Linked Main EC to institution {institution.short_name or institution.name}'
                )
            )
        elif role_name == 'admin' and not institution:
            self.stdout.write(
                self.style.WARNING(
                    'No --institution-code given. User can log in, but Main EC '
                    'governance needs an institution link. Re-run with --institution-code.'
                )
            )

        self.stdout.write(f'{"Created" if created else "Updated"}: {user.email} uuid={user.uuid}')
