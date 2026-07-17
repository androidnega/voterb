from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import ECMembership, ECUnit, Role, User
from accounts.org import get_or_create_main_ec_unit
from system.models import InstitutionProfile


class Command(BaseCommand):
    help = (
        'Bootstrap institution hierarchy: ensure a default institution exists, '
        'create its Main EC unit, and attach existing admin users.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--name', default='Takoradi Technical University')
        parser.add_argument('--short-name', default='TTU')
        parser.add_argument('--code', default='TTU')

    @transaction.atomic
    def handle(self, *args, **options):
        Role.objects.get_or_create(name='admin', defaults={'description': 'Main Electoral Commission'})
        Role.objects.get_or_create(name='sub_ec', defaults={'description': 'Sub Electoral Commission'})
        Role.objects.get_or_create(name='auditor', defaults={'description': 'Auditor'})

        institution = InstitutionProfile.objects.order_by('created_at', 'name').first()
        if not institution:
            institution = InstitutionProfile.objects.create(
                name=options['name'],
                short_name=options['short_name'],
                code=options['code'],
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS(f'Created institution {institution.name}'))
        else:
            changed = []
            if not institution.code:
                institution.code = options['code']
                changed.append('code')
            if not institution.short_name:
                institution.short_name = options['short_name']
                changed.append('short_name')
            if changed:
                institution.save(update_fields=[*changed, 'updated_at'])
            self.stdout.write(f'Using institution {institution.name}')

        main_unit = get_or_create_main_ec_unit(institution)
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
            f'Done. Attached {attached} admin user(s) to Main EC. '
            f'Sub EC units: {ECUnit.objects.filter(institution=institution, unit_type=ECUnit.UNIT_SUB).count()}'
        ))
