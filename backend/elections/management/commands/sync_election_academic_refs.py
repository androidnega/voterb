from django.core.management.base import BaseCommand

from candidates.models import Candidate
from elections.models import Election
from elections.services.academic_refs import sync_candidate_department


class Command(BaseCommand):
    help = 'Link election candidates to the current active faculty/department structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--election-title',
            default='TTU SRC Elections 2026',
            help='Election title to sync (default: TTU SRC Elections 2026)',
        )
        parser.add_argument(
            '--all-elections',
            action='store_true',
            help='Sync candidates for every election',
        )

    def handle(self, *args, **options):
        if options['all_elections']:
            elections = Election.objects.all().order_by('title')
        else:
            elections = Election.objects.filter(title=options['election_title'])
            if not elections.exists():
                self.stderr.write(self.style.ERROR(f"No election titled '{options['election_title']}'"))
                return

        updated = 0
        skipped = 0

        for election in elections:
            candidates = Candidate.objects.filter(election=election)
            for candidate in candidates.select_related('academic_department', 'faculty'):
                needs_sync = (
                    not candidate.academic_department_id
                    or not candidate.faculty_id
                    or not candidate.academic_department.is_active
                    or not candidate.faculty.is_active
                    or candidate.department != candidate.academic_department.name
                )
                if not needs_sync:
                    continue

                if sync_candidate_department(candidate):
                    updated += 1
                    self.stdout.write(
                        f"  {candidate.full_name} → {candidate.academic_department.name} "
                        f"({candidate.faculty.name})"
                    )
                else:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(
                        f"  Could not map {candidate.full_name!r} department {candidate.department!r}"
                    ))

            # Clear election scope if it points at deactivated structure
            scope_changed = False
            if election.scope_faculty_id and not election.scope_faculty.is_active:
                election.scope_faculty = None
                scope_changed = True
            if election.scope_department_id and not election.scope_department.is_active:
                election.scope_department = None
                scope_changed = True
            if scope_changed:
                election.save(update_fields=['scope_faculty', 'scope_department', 'updated_at'])
                self.stdout.write(self.style.WARNING(f"Cleared inactive scope on {election.title}"))

        self.stdout.write(self.style.SUCCESS(f'Synced {updated} candidate(s); {skipped} unmappable'))
