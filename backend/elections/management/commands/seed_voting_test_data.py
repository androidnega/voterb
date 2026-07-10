from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, Role
from elections.models import Election, VoterEligibility, Position
from candidates.models import Candidate

class Command(BaseCommand):
    help = 'Seed test data for voting (student, election, eligibility, candidates)'

    def handle(self, *args, **options):
        # 1. Get or create student role
        student_role, _ = Role.objects.get_or_create(name='student')

        # 2. Create a student user
        student, created = User.objects.get_or_create(
            email='student@voterb.com',
            defaults={
                'index_number': 'BC/ITS/24/001',
                'first_name': 'Test',
                'last_name': 'Student',
                'phone_number': '+233501234567',
                'role': student_role,
                'is_verified': True,
                'is_active': True,
            }
        )
        if created:
            student.set_password('student123')
            student.save()
            self.stdout.write(self.style.SUCCESS(f'Student created: {student.email}'))
        else:
            self.stdout.write(self.style.WARNING(f'Student already exists: {student.email}'))

        # 3. Get or create an admin user (if not exists)
        admin_user = User.objects.filter(email='admin@voterb.com').first()
        if not admin_user:
            admin_role = Role.objects.get(name='admin')
            admin_user = User.objects.create_superuser(
                email='admin@voterb.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                role=admin_role,
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS('Admin created'))

        # 4. Get or create an open election
        election, created = Election.objects.get_or_create(
            title='TTU SRC Elections 2026',
            defaults={
                'description': 'Student Representative Council elections',
                'election_type': 'student_union',
                'status': 'open',
                'start_date': timezone.now() - timedelta(days=1),
                'end_date': timezone.now() + timedelta(days=7),
                'created_by': admin_user,
                'allow_web_voting': True,
                'allow_ussd_voting': False,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Election created: {election.title}'))
        else:
            self.stdout.write(self.style.WARNING(f'Election already exists: {election.title}'))

        # 5. Ensure the student is eligible for this election
        eligibility, created = VoterEligibility.objects.get_or_create(
            election=election,
            user=student,
            defaults={'is_eligible': True, 'verified_by': admin_user, 'verified_at': timezone.now()}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Eligibility created for {student.email}'))
        else:
            self.stdout.write(self.style.WARNING(f'Eligibility already exists for {student.email}'))

        # 6. Create a position if not exists
        position, created = Position.objects.get_or_create(
            election=election,
            title='President',
            defaults={
                'max_votes_allowed': 1,
                'display_order': 1,
                'is_active': True,
                'is_votable': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Position created: President'))
        else:
            self.stdout.write(self.style.WARNING('Position already exists: President'))

        # 7. Create candidates if not exists
        candidates_data = [
            {'full_name': 'John Doe', 'department': 'Computer Science', 'ballot_number': 1},
            {'full_name': 'Jane Smith', 'department': 'Engineering', 'ballot_number': 2},
            {'full_name': 'Kwame Nkrumah', 'department': 'Business', 'ballot_number': 3},
        ]
        for data in candidates_data:
            candidate, created = Candidate.objects.get_or_create(
                election=election,
                position=position,
                full_name=data['full_name'],
                defaults={
                    'department': data['department'],
                    'ballot_number': data['ballot_number'],
                    'status': 'approved'
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Candidate created: {candidate.full_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Candidate already exists: {candidate.full_name}'))

        self.stdout.write(self.style.SUCCESS('✅ Test data seeding complete!'))
        self.stdout.write(self.style.SUCCESS(f'Student login: student@voterb.com / student123'))
        self.stdout.write(self.style.SUCCESS(f'Admin login: admin@voterb.com / admin123'))
