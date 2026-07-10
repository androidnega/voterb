from django.core.management.base import BaseCommand
from accounts.models import Role

class Command(BaseCommand):
    help = 'Seed default roles'

    def handle(self, *args, **options):
        roles = ['student', 'candidate', 'admin', 'super_admin']
        for role_name in roles:
            Role.objects.get_or_create(name=role_name)
        self.stdout.write(self.style.SUCCESS('Roles seeded.'))
