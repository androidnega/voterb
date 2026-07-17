from django.core.management.base import BaseCommand
from accounts.models import Role

class Command(BaseCommand):
    help = 'Seed default roles'

    def handle(self, *args, **options):
        roles = [
            ('student', 'Student voter'),
            ('candidate', 'Election candidate'),
            ('admin', 'Main Electoral Commission'),
            ('sub_ec', 'Sub Electoral Commission (faculty/department)'),
            ('auditor', 'Auditor'),
            ('super_admin', 'Platform Super Admin'),
        ]
        for role_name, description in roles:
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': description},
            )
            if not created and not role.description:
                role.description = description
                role.save(update_fields=['description', 'updated_at'])
        self.stdout.write(self.style.SUCCESS('Roles seeded.'))
