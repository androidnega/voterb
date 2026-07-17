"""Ensure a staff (Main EC / Super Admin) account exists — does not touch settings or .env."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

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
            help='Optional institution code (e.g. TTU). Links Main EC to that institution.',
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

        code = (options['institution_code'] or '').strip()
        if code and role_name == 'admin':
            institution = InstitutionProfile.objects.filter(code__iexact=code).first()
            if not institution:
                raise CommandError(f'Institution with code {code!r} not found')
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

        self.stdout.write(f'{"Created" if created else "Updated"}: {user.email} uuid={user.uuid}')
