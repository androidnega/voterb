import csv
import hashlib
import random
import shutil
from datetime import timedelta
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User, Role
from candidates.models import Candidate
from elections.models import Election, Position, VoterEligibility, VotingChannel
from elections.services.academic_refs import resolve_department, apply_department_to_candidate
from voting.models import Vote

DATA_DIR = Path(__file__).resolve().parents[3] / 'data'
PHOTOS_DIR = DATA_DIR / 'candidate_photos'

FEMALE_PHOTOS = [
    'image-2082c7b8-e758-440d-b660-47ef5ae733f4.png',
    'image-296a558f-9ec6-4479-baeb-bf662c850848.png',
    'image-d077bcad-f335-4aa2-abb7-b20ca70b1462.png',
]

MALE_PHOTOS = [
    'image-ea06f46d-2813-4f0e-a3c3-cfd1b3777879.png',
    'image-26dce426-8d03-4503-8b24-236e7631a464.png',
    'image-a85d0336-d00f-4bae-9957-7bf3fd84b255.png',
]

CANDIDATE_ROSTER = [
    {'position': 'President', 'full_name': 'John Doe', 'department_code': 'CSC', 'gender': 'male', 'ballot_number': 1},
    {'position': 'President', 'full_name': 'Jane Smith', 'department_code': 'MEC', 'gender': 'female', 'ballot_number': 2},
    {'position': 'President', 'full_name': 'Kwame Nkrumah', 'department_code': 'MKT', 'gender': 'male', 'ballot_number': 3},
    {'position': 'Vice President', 'full_name': 'Ama Serwaa', 'department_code': 'CSC', 'gender': 'female', 'ballot_number': 1},
    {'position': 'Vice President', 'full_name': 'Emmanuel Agyekum', 'department_code': 'EEE', 'gender': 'male', 'ballot_number': 2},
    {'position': 'Secretary', 'full_name': 'Grace Amoah', 'department_code': 'LBS', 'gender': 'female', 'ballot_number': 1},
    {'position': 'Secretary', 'full_name': 'Isaac Tetteh', 'department_code': 'LBS', 'gender': 'male', 'ballot_number': 2},
    {'position': 'Treasurer', 'full_name': 'Patience Quaye', 'department_code': 'ACF', 'gender': 'female', 'ballot_number': 1},
    {'position': 'Treasurer', 'full_name': 'Samuel Annan', 'department_code': 'ACF', 'gender': 'male', 'ballot_number': 2},
]



class Command(BaseCommand):
    help = 'Seed election with real candidate photos, voter index CSV, and live vote data'

    def add_arguments(self, parser):
        parser.add_argument('--election-title', default='TTU SRC Elections 2026')

    def handle(self, *args, **options):
        for role_name in ['student', 'candidate', 'admin', 'super_admin', 'auditor']:
            Role.objects.get_or_create(name=role_name)

        student_role = Role.objects.get(name='student')
        admin_role = Role.objects.get(name='admin')

        ec_admin, _ = User.objects.get_or_create(
            email='election@voterb.com',
            defaults={
                'first_name': 'Election',
                'last_name': 'Officer',
                'role': admin_role,
                'is_staff': True,
                'is_verified': True,
                'is_active': True,
            },
        )
        ec_admin.set_password('admin123')
        ec_admin.role = admin_role
        ec_admin.is_staff = True
        ec_admin.save()

        election, _ = Election.objects.get_or_create(
            title=options['election_title'],
            defaults={
                'description': 'Student Representative Council elections',
                'election_type': 'student_union',
                'status': 'open',
                'start_date': timezone.now() - timedelta(days=1),
                'end_date': timezone.now() + timedelta(days=7),
                'created_by': ec_admin,
                'allow_web_voting': True,
                'demo_seed': True,
            },
        )
        election.status = 'open'
        election.demo_seed = True
        election.save()

        web_channel, _ = VotingChannel.objects.get_or_create(channel_name='web')

        # Import eligible voters from CSV
        csv_path = DATA_DIR / 'eligible_voters.csv'
        voters_created = 0
        eligibility_created = 0

        with open(csv_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                index_number = row['index_number'].strip()
                first_name = row.get('first_name', '').strip() or 'Student'
                last_name = row.get('last_name', '').strip() or index_number.split('/')[-1]
                user, created = User.objects.get_or_create(
                    index_number=index_number,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': student_role,
                        'is_verified': True,
                        'is_active': True,
                        'demo_seed': True,
                    },
                )
                if created:
                    user.set_password('student123')
                    user.save()
                    voters_created += 1
                else:
                    user.first_name = first_name
                    user.last_name = last_name
                    user.email = None
                    user.role = student_role
                    user.is_active = True
                    user.save()

                _, elig_created = VoterEligibility.objects.get_or_create(
                    election=election,
                    user=user,
                    defaults={
                        'is_eligible': True,
                        'verified_by': ec_admin,
                        'verified_at': timezone.now(),
                    },
                )
                if elig_created:
                    eligibility_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Voters: {voters_created} new, {eligibility_created} eligibility records added'
        ))

        csv_indices = set()
        with open(csv_path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            csv_indices = {row['index_number'].strip() for row in reader}

        removed_eligibility = VoterEligibility.objects.filter(election=election).exclude(
            user__index_number__in=csv_indices
        ).delete()[0]

        roster_titles = {entry['position'] for entry in CANDIDATE_ROSTER}
        roster_names = {entry['full_name'] for entry in CANDIDATE_ROSTER}
        Position.objects.filter(election=election).exclude(title__in=roster_titles).update(
            is_active=False, is_votable=False
        )
        Vote.objects.filter(election=election).delete()
        removed_candidates = Candidate.objects.filter(election=election).exclude(
            full_name__in=roster_names
        ).delete()[0]

        if removed_eligibility or removed_candidates:
            self.stdout.write(self.style.WARNING(
                f'Cleanup: removed {removed_eligibility} stale eligibility, {removed_candidates} orphan candidates'
            ))

        # Assign gender-matched photos to candidates
        random.shuffle(FEMALE_PHOTOS)
        random.shuffle(MALE_PHOTOS)
        female_pool = list(FEMALE_PHOTOS)
        male_pool = list(MALE_PHOTOS)

        media_photo_dir = Path(__file__).resolve().parents[3] / 'media' / 'candidate_photos'
        media_photo_dir.mkdir(parents=True, exist_ok=True)

        candidates_seeded = 0
        for entry in CANDIDATE_ROSTER:
            pos, _ = Position.objects.get_or_create(
                election=election,
                title=entry['position'],
                defaults={
                    'max_votes_allowed': 1,
                    'display_order': 1,
                    'is_active': True,
                    'is_votable': True,
                },
            )
            pos.is_active = True
            pos.is_votable = True
            pos.save()

            department = resolve_department(code=entry['department_code'])
            if not department:
                self.stderr.write(self.style.ERROR(
                    f"Unknown department code {entry['department_code']!r} for {entry['full_name']}"
                ))
                continue

            candidate, _ = Candidate.objects.get_or_create(
                election=election,
                position=pos,
                full_name=entry['full_name'],
                defaults={
                    'department': department.name,
                    'ballot_number': entry['ballot_number'],
                    'status': 'approved',
                    'faculty': department.faculty,
                    'academic_department': department,
                },
            )
            candidate.ballot_number = entry['ballot_number']
            candidate.status = 'approved'
            apply_department_to_candidate(candidate, department)

            pool = female_pool if entry['gender'] == 'female' else male_pool
            if not pool:
                pool = FEMALE_PHOTOS if entry['gender'] == 'female' else MALE_PHOTOS
            photo_file = pool.pop(0) if pool else random.choice(
                FEMALE_PHOTOS if entry['gender'] == 'female' else MALE_PHOTOS
            )

            src = PHOTOS_DIR / photo_file
            if src.exists():
                dest_name = f"{candidate.uuid}.png"
                dest = media_photo_dir / dest_name
                shutil.copy2(src, dest)
                with open(dest, 'rb') as img_fh:
                    candidate.photo.save(dest_name, File(img_fh), save=True)
                candidates_seeded += 1

        # Distribute votes across eligible voters
        eligible_users = list(
            User.objects.filter(
                votereligibility__election=election,
                votereligibility__is_eligible=True,
            ).distinct()
        )
        all_candidates = list(
            Candidate.objects.filter(election=election, status='approved').select_related('position')
        )

        vote_count = 0
        total_positions = Position.objects.filter(election=election, is_active=True).count() or 1
        for i, voter in enumerate(eligible_users):
            # Each voter casts one vote per position (pick candidate by rotation)
            positions_voted = set()
            for cand in all_candidates:
                if cand.position_id in positions_voted:
                    continue
                pos_candidates = [c for c in all_candidates if c.position_id == cand.position_id]
                chosen = pos_candidates[i % len(pos_candidates)]
                vote_hash = hashlib.sha256(
                    f'{voter.uuid}{election.uuid}{chosen.uuid}{i}'.encode()
                ).hexdigest()
                days_ago = (i * total_positions + len(positions_voted)) % 7
                vote_time = timezone.now() - timedelta(days=days_ago, hours=(i % 12))
                Vote.objects.create(
                    user=voter,
                    election=election,
                    position=chosen.position,
                    candidate=chosen,
                    channel=web_channel,
                    vote_hash=vote_hash,
                    timestamp=vote_time,
                )
                positions_voted.add(chosen.position_id)
                vote_count += 1

        self.stdout.write(self.style.SUCCESS(f'Candidates with photos: {candidates_seeded}'))
        self.stdout.write(self.style.SUCCESS(f'Live votes seeded: {vote_count}'))
        self.stdout.write(self.style.SUCCESS(f'Election UUID: {election.uuid}'))
        self.stdout.write(self.style.SUCCESS(f'Monitor: /monitor/{election.uuid}'))
