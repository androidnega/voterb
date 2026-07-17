import hashlib
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, Role
from elections.models import Election, VoterEligibility, Position, VotingChannel
from candidates.models import Candidate
from voting.models import Vote


class Command(BaseCommand):
    help = 'Seed test data for voting (student, election, eligibility, candidates, sample votes)'

    def handle(self, *args, **options):
        for role_name in ['student', 'candidate', 'admin', 'super_admin', 'auditor']:
            Role.objects.get_or_create(name=role_name)

        student_role = Role.objects.get(name='student')
        admin_role = Role.objects.get(name='admin')

        student, created = User.objects.get_or_create(
            index_number='BC/ITS/24/001',
            defaults={
                'first_name': 'Test',
                'last_name': 'Student',
                'phone_number': '+233501234567',
                'role': student_role,
                'is_verified': True,
                'is_active': True,
            },
        )
        if created:
            student.set_password('student123')
            student.save()
            self.stdout.write(self.style.SUCCESS(f'Student created: {student.index_number}'))
        else:
            student.email = None
            student.save(update_fields=['email'])
            self.stdout.write(self.style.WARNING(f'Student already exists: {student.index_number}'))

        ec_admin, created = User.objects.get_or_create(
            email='election@voterb.com',
            defaults={
                'first_name': 'Election',
                'last_name': 'Admin',
                'phone_number': '+233501234568',
                'role': admin_role,
                'is_staff': True,
                'is_superuser': False,
                'is_verified': True,
                'is_active': True,
            },
        )
        ec_admin.set_password('admin123')
        ec_admin.role = admin_role
        ec_admin.is_staff = True
        ec_admin.is_superuser = False
        ec_admin.is_active = True
        ec_admin.save()
        if created:
            self.stdout.write(self.style.SUCCESS('Election admin created: election@voterb.com'))
        else:
            self.stdout.write(self.style.WARNING('Election admin updated: election@voterb.com'))

        super_admin = User.objects.filter(email='admin@voterb.com').first()
        if not super_admin:
            super_role = Role.objects.get(name='super_admin')
            super_admin = User.objects.create_superuser(
                email='admin@voterb.com',
                password='admin123',
                first_name='Super',
                last_name='Admin',
                role=super_role,
                is_verified=True,
            )
            self.stdout.write(self.style.SUCCESS('Super admin created: admin@voterb.com'))

        web_channel, _ = VotingChannel.objects.get_or_create(channel_name='web')

        election, created = Election.objects.get_or_create(
            title='TTU SRC Elections 2026',
            defaults={
                'description': 'Student Representative Council elections — live monitor demo',
                'status': 'open',
                'start_date': timezone.now() - timedelta(days=1),
                'end_date': timezone.now() + timedelta(days=7),
                'created_by': ec_admin,
                'allow_web_voting': True,
                'allow_ussd_voting': False,
                'demo_seed': True,
            },
        )
        if not created:
            election.status = 'open'
            election.demo_seed = True
            election.start_date = timezone.now() - timedelta(days=1)
            election.end_date = timezone.now() + timedelta(days=7)
            election.save()
            self.stdout.write(self.style.WARNING(f'Election updated: {election.title}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Election created: {election.title}'))

        extra_students = [
            ('BC/ITS/24/002', 'Ama', 'Serwaa'),
            ('BC/ITS/24/003', 'Kofi', 'Boateng'),
            ('BC/ITS/24/004', 'Akosua', 'Mensah'),
            ('BC/ITS/24/005', 'Emmanuel', 'Agyekum'),
        ]
        voters = [student]
        for index, first, last in extra_students:
            voter, voter_created = User.objects.get_or_create(
                index_number=index,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'role': student_role,
                    'is_verified': True,
                    'is_active': True,
                },
            )
            if voter_created:
                voter.set_password('student123')
                voter.save()
            else:
                voter.email = None
                voter.save(update_fields=['email'])
            voters.append(voter)
            VoterEligibility.objects.get_or_create(
                election=election,
                user=voter,
                defaults={
                    'is_eligible': True,
                    'verified_by': ec_admin,
                    'verified_at': timezone.now(),
                },
            )

        positions_data = [
            ('President', 1),
            ('Vice President', 2),
        ]
        positions = []
        for title, order in positions_data:
            pos, pos_created = Position.objects.get_or_create(
                election=election,
                title=title,
                defaults={
                    'max_votes_allowed': 1,
                    'display_order': order,
                    'is_active': True,
                    'is_votable': True,
                },
            )
            positions.append(pos)
            if pos_created:
                self.stdout.write(self.style.SUCCESS(f'Position created: {title}'))

        president_candidates = [
            {'full_name': 'John Doe', 'department_code': 'CSC', 'ballot_number': 1},
            {'full_name': 'Jane Smith', 'department_code': 'MEC', 'ballot_number': 2},
            {'full_name': 'Kwame Nkrumah', 'department_code': 'MKT', 'ballot_number': 3},
        ]
        vice_candidates = [
            {'full_name': 'Ama Serwaa', 'department_code': 'CSC', 'ballot_number': 1},
            {'full_name': 'Emmanuel Agyekum', 'department_code': 'EEE', 'ballot_number': 2},
        ]

        def upsert_candidate(position, data):
            candidate, _ = Candidate.objects.get_or_create(
                election=election,
                position=position,
                full_name=data['full_name'],
                defaults={
                    'ballot_number': data['ballot_number'],
                    'status': 'approved',
                },
            )
            candidate.ballot_number = data['ballot_number']
            candidate.status = 'approved'
            candidate.save(update_fields=['ballot_number', 'status', 'updated_at'])
            return candidate

        all_candidates = []
        for data in president_candidates:
            candidate = upsert_candidate(positions[0], data)
            if candidate:
                all_candidates.append((positions[0], candidate))

        for data in vice_candidates:
            candidate = upsert_candidate(positions[1], data)
            if candidate:
                all_candidates.append((positions[1], candidate))

        if election.demo_seed:
            Vote.objects.filter(election=election).delete()

        president_cands = [c for p, c in all_candidates if p.title == 'President']
        vice_cands = [c for p, c in all_candidates if p.title == 'Vice President']

        for i, voter in enumerate(voters):
            pres_candidate = president_cands[i % len(president_cands)]
            vice_candidate = vice_cands[i % len(vice_cands)]

            for pos, candidate in [(positions[0], pres_candidate), (positions[1], vice_candidate)]:
                vote_hash = hashlib.sha256(
                    f'{voter.uuid}{election.uuid}{pos.uuid}{candidate.uuid}{i}'.encode()
                ).hexdigest()
                Vote.objects.create(
                    user=voter,
                    election=election,
                    position=pos,
                    candidate=candidate,
                    channel=web_channel,
                    vote_hash=vote_hash,
                )

        self.stdout.write(self.style.SUCCESS('✅ Test data seeding complete!'))
        self.stdout.write(self.style.SUCCESS(f'Election UUID: {election.uuid}'))
        self.stdout.write(self.style.SUCCESS(f'Monitor room: /monitor/{election.uuid}'))
        self.stdout.write(self.style.SUCCESS('EC Admin login: election@voterb.com / admin123'))
        self.stdout.write(self.style.SUCCESS('Super Admin login: admin@voterb.com / admin123'))
        self.stdout.write(self.style.SUCCESS('Student login: BC/ITS/24/001 (index number, OTP)'))
