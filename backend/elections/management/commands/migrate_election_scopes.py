"""One-time conversion from legacy election scopes to voter registers.

The current branch has already removed the Python model fields
(`scope_type`, `scope_faculty`, `scope_department`, `scope_level`), so this
command reads legacy columns defensively with raw SQL when they still exist.
If the columns are already gone, it still links an election to an existing
register or creates a register from legacy VoterEligibility rows.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction

from accounts.models import User
from elections.models import (
    Department,
    Election,
    Faculty,
    VoterCategory,
    VoterEligibility,
    VoterRegister,
    VoterRegisterEntry,
)
from elections.services.register_service import sync_eligibility_from_registers


class Command(BaseCommand):
    help = 'Convert old scope-based elections to primary voter registers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be converted without writing changes.',
        )

    def _election_columns(self):
        with connection.cursor() as cursor:
            return {
                col.name
                for col in connection.introspection.get_table_description(
                    cursor,
                    Election._meta.db_table,
                )
            }

    def _legacy_scope_row(self, election_id, columns):
        wanted = ['scope_type', 'scope_faculty_id', 'scope_department_id', 'scope_level_id']
        if not set(wanted).issubset(columns):
            return {}
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT scope_type, scope_faculty_id, scope_department_id, scope_level_id
                FROM elections_election
                WHERE id = %s
                """,
                [election_id],
            )
            row = cursor.fetchone()
        if not row:
            return {}
        return dict(zip(wanted, row))

    def _label_for_scope(self, scope):
        scope_type = scope.get('scope_type') or 'school'
        if scope_type == 'faculty' and scope.get('scope_faculty_id'):
            faculty = Faculty.objects.filter(pk=scope['scope_faculty_id']).first()
            return faculty.name if faculty else 'Faculty Register'
        if scope_type == 'department' and scope.get('scope_department_id'):
            department = Department.objects.filter(pk=scope['scope_department_id']).first()
            return department.name if department else 'Department Register'
        if scope_type == 'level' and scope.get('scope_level_id'):
            return 'Legacy Level Register'
        return 'All Students'

    def _users_for_scope(self, election, scope):
        eligibility_users = User.objects.filter(
            votereligibility__election=election,
            votereligibility__is_eligible=True,
        ).distinct()
        if eligibility_users.exists():
            return eligibility_users

        qs = User.objects.filter(is_active=True)
        qs = qs.filter(role__name__in=['student', 'candidate'])
        scope_type = scope.get('scope_type') or 'school'
        if scope_type == 'faculty' and scope.get('scope_faculty_id'):
            qs = qs.filter(faculty_id=scope['scope_faculty_id'])
        elif scope_type == 'department' and scope.get('scope_department_id'):
            qs = qs.filter(department_id=scope['scope_department_id'])
        elif scope_type == 'level' and scope.get('scope_level_id'):
            # Study levels removed — fall back to all students / eligibility rows.
            pass
        return qs

    def _full_name(self, user):
        name = f'{user.first_name or ""} {user.last_name or ""}'.strip()
        return name or user.index_number or user.email or str(user.uuid)

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        columns = self._election_columns()
        converted = 0
        skipped = 0

        for election in Election.objects.all().order_by('created_at'):
            if election.register_id:
                skipped += 1
                self.stdout.write(f'Skip {election.title}: already linked to a register')
                continue

            existing_register = election.registers.order_by('created_at').first()
            if existing_register:
                if not dry_run:
                    election.register = existing_register
                    election.save(update_fields=['register', 'updated_at'])
                    sync_eligibility_from_registers(election)
                converted += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Linked {election.title} to existing register {existing_register.name}'
                    )
                )
                continue

            scope = self._legacy_scope_row(election.id, columns)
            label = self._label_for_scope(scope)
            users = list(self._users_for_scope(election, scope))
            self.stdout.write(
                f'Create register "{label}" for {election.title}: {len(users)} voter(s)'
            )
            if dry_run:
                converted += 1
                continue

            register = VoterRegister.objects.create(
                election=election,
                name=label,
                description='Migrated from legacy election scope',
            )
            category, _ = VoterCategory.objects.get_or_create(
                register=register,
                name=label,
                defaults={'description': 'Migrated default category'},
            )
            for user in users:
                voter_id = user.index_number or str(user.uuid)
                VoterRegisterEntry.objects.update_or_create(
                    register=register,
                    voter_id=voter_id,
                    defaults={
                        'category': category,
                        'full_name': self._full_name(user),
                        'user': user,
                    },
                )
            election.register = register
            election.save(update_fields=['register', 'updated_at'])
            sync_eligibility_from_registers(election)
            converted += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Migration complete: {converted} converted/linked, {skipped} skipped.'
            )
        )
