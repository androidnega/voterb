from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import ECMembership, ECUnit, Role, User
from accounts.org import get_or_create_main_ec_unit
from system.models import InstitutionProfile


class Command(BaseCommand):
    help = (
        'Bootstrap institution hierarchy: ensure the target institution exists '
        '(by code), create its Main EC unit, and attach existing admin users.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--name', default='Takoradi Technical University')
        parser.add_argument('--short-name', default='TTU')
        parser.add_argument('--code', default='TTU')
        parser.add_argument(
            '--rename',
            action='store_true',
            help='Force-update name/short_name on the institution matched by code.',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        Role.objects.get_or_create(name='admin', defaults={'description': 'Main Electoral Commission'})
        Role.objects.get_or_create(name='sub_ec', defaults={'description': 'Sub Electoral Commission'})
        Role.objects.get_or_create(name='auditor', defaults={'description': 'Auditor'})

        code = (options['code'] or 'TTU').strip().upper()
        name = options['name']
        short_name = options['short_name']

        institution = InstitutionProfile.objects.filter(code__iexact=code).first()
        if not institution:
            # Prefer renaming a placeholder "VoterB" / first empty-code row over creating a duplicate.
            placeholder = (
                InstitutionProfile.objects.filter(code__iexact='TTU').first()
                or InstitutionProfile.objects.filter(name__iexact='VoterB').first()
                or InstitutionProfile.objects.filter(short_name__iexact='TTU').first()
            )
            if placeholder:
                institution = placeholder
            else:
                institution = InstitutionProfile.objects.create(
                    name=name,
                    short_name=short_name,
                    code=code,
                    is_active=True,
                )
                self.stdout.write(self.style.SUCCESS(f'Created institution {institution.name}'))

        changed = []
        if institution.code != code:
            institution.code = code
            changed.append('code')
        if options['rename'] or institution.name in ('', 'VoterB') or not institution.name:
            if institution.name != name:
                institution.name = name
                changed.append('name')
        if options['rename'] or not institution.short_name or institution.short_name == 'VoterB':
            if institution.short_name != short_name:
                institution.short_name = short_name
                changed.append('short_name')
        if not institution.is_active:
            institution.is_active = True
            changed.append('is_active')
        if changed:
            institution.save(update_fields=[*changed, 'updated_at'])
            self.stdout.write(self.style.SUCCESS(
                f'Updated institution fields: {", ".join(changed)} → {institution.name} ({institution.code})'
            ))
        else:
            self.stdout.write(f'Using institution {institution.name} ({institution.code})')

        main_unit = get_or_create_main_ec_unit(institution)
        # Keep Main EC display name aligned with institution short name
        expected_ec_name = f'{institution.short_name or institution.code} EC'
        if main_unit.name != expected_ec_name:
            main_unit.name = expected_ec_name
            main_unit.save(update_fields=['name', 'updated_at'])
        self.stdout.write(f'Main EC unit: {main_unit.name}')

        admin_role = Role.objects.filter(name='admin').first()
        attached = 0
        if admin_role:
            for user in User.objects.filter(role=admin_role):
                if not user.institution_id:
                    user.institution = institution
                    user.save(update_fields=['institution', 'updated_at'])
                _, created = ECMembership.objects.get_or_create(
                    user=user,
                    ec_unit=main_unit,
                    defaults={'is_active': True},
                )
                if created:
                    attached += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Institution={institution.uuid} MainEC={main_unit.uuid}. '
            f'Attached {attached} admin user(s). '
            f'Sub EC units: {ECUnit.objects.filter(institution=institution, unit_type=ECUnit.UNIT_SUB).count()}'
        ))
