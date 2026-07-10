import hashlib
import random
from datetime import timedelta
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction

from accounts.permissions import IsAdminOrSuperAdmin
from elections.models import Election, VoterEligibility, Position
from candidates.models import Candidate
from voting.models import Vote
from security.models import SVTToken
from accounts.models import User

# Helper to generate SVT
def generate_svt():
    return f"{random.randint(100000, 999999)}"

# ----- GET /api/v1/voting/eligible/ -----
class EligibleElectionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        eligibilities = VoterEligibility.objects.filter(
            user=user,
            is_eligible=True,
            election__status='open'
        ).select_related('election')
        
        elections_data = []
        for el in eligibilities:
            election = el.election
            elections_data.append({
                'uuid': election.uuid,
                'title': election.title,
                'description': election.description,
                'status': election.status,
                'start_date': election.start_date,
                'end_date': election.end_date,
                'voter_count': VoterEligibility.objects.filter(election=election, is_eligible=True).count()
            })
        return Response(elections_data)

# ----- POST /api/v1/voting/elections/<uuid>/svt/request/ -----
class SVTRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user

        if election.status != 'open':
            return Response({'error': 'Election is not open'}, status=status.HTTP_400_BAD_REQUEST)

        if not VoterEligibility.objects.filter(user=user, election=election, is_eligible=True).exists():
            return Response({'error': 'You are not eligible for this election'}, status=status.HTTP_403_FORBIDDEN)

        existing = SVTToken.objects.filter(
            user=user,
            election=election,
            status__in=['issued', 'validated']
        ).first()
        if existing:
            existing.status = 'expired'
            existing.save()

        code = generate_svt()
        hashed = hashlib.sha256(code.encode()).hexdigest()
        expires_at = timezone.now() + timedelta(minutes=10)
        svt = SVTToken.objects.create(
            user=user,
            election=election,
            token_hash=hashed,
            status='issued',
            expires_at=expires_at
        )

        print(f"🔑 SVT for {user.email} (election: {election.title}): {code}")

        return Response({'message': 'SVT sent to your phone', 'svt_id': svt.svt_id})

# ----- POST /api/v1/voting/elections/<uuid>/svt/validate/ -----
class SVTValidateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user
        svt_code = request.data.get('svt_code')

        if not svt_code:
            return Response({'error': 'SVT code required'}, status=status.HTTP_400_BAD_REQUEST)

        svt = SVTToken.objects.filter(
            user=user,
            election=election,
            status='issued'
        ).first()

        if not svt:
            return Response({'error': 'No valid SVT found. Request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        if timezone.now() > svt.expires_at:
            svt.status = 'expired'
            svt.save()
            return Response({'error': 'SVT expired. Request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        hashed = hashlib.sha256(svt_code.encode()).hexdigest()
        if hashed != svt.token_hash:
            svt.validation_attempts += 1
            svt.save()
            return Response({'error': 'Invalid SVT code'}, status=status.HTTP_400_BAD_REQUEST)

        svt.status = 'validated'
        svt.validated_at = timezone.now()
        svt.save()

        return Response({'message': 'SVT validated successfully'})

# ----- GET /api/v1/voting/elections/<uuid>/ballot/ -----
class BallotView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user

        if election.status != 'open':
            return Response({'error': 'Election is not open'}, status=status.HTTP_400_BAD_REQUEST)

        svt = SVTToken.objects.filter(
            user=user,
            election=election,
            status='validated'
        ).first()
        if not svt:
            return Response({'error': 'Valid SVT required'}, status=status.HTTP_400_BAD_REQUEST)

        positions = Position.objects.filter(
            election=election,
            is_active=True,
            is_votable=True
        ).order_by('display_order').prefetch_related('candidates')

        ballot_data = []
        for pos in positions:
            candidates = pos.candidates.filter(status='approved').order_by('ballot_number')
            ballot_data.append({
                'uuid': pos.uuid,
                'title': pos.title,
                'description': pos.description,
                'max_votes_allowed': pos.max_votes_allowed,
                'candidates': [
                    {
                        'uuid': c.uuid,
                        'full_name': c.full_name,
                        'department': c.department,
                        'ballot_number': c.ballot_number,
                        'photo': c.photo.url if c.photo else None
                    } for c in candidates
                ]
            })

        return Response({'positions': ballot_data})

# ----- POST /api/v1/voting/elections/<uuid>/submit/ -----
class SubmitVoteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        user = request.user
        svt_code = request.data.get('svt_code')
        selections = request.data.get('selections', [])

        if not svt_code:
            return Response({'error': 'SVT code required'}, status=status.HTTP_400_BAD_REQUEST)

        svt = SVTToken.objects.filter(
            user=user,
            election=election,
            status='validated'
        ).first()
        if not svt:
            return Response({'error': 'Valid SVT required'}, status=status.HTTP_400_BAD_REQUEST)

        hashed = hashlib.sha256(svt_code.encode()).hexdigest()
        if hashed != svt.token_hash:
            return Response({'error': 'Invalid SVT code'}, status=status.HTTP_400_BAD_REQUEST)

        if election.status != 'open':
            return Response({'error': 'Election is not open'}, status=status.HTTP_400_BAD_REQUEST)

        votes_created = []
        for sel in selections:
            position_uuid = sel.get('position_uuid')
            candidate_uuids = sel.get('candidate_uuids', [])

            position = get_object_or_404(Position, uuid=position_uuid, election=election)
            if not position.is_votable:
                return Response({'error': f'Position {position.title} is not votable'}, status=status.HTTP_400_BAD_REQUEST)

            if len(candidate_uuids) > position.max_votes_allowed:
                return Response({'error': f'Too many candidates selected for {position.title}'}, status=status.HTTP_400_BAD_REQUEST)

            for candidate_uuid in candidate_uuids:
                candidate = get_object_or_404(Candidate, uuid=candidate_uuid, position=position, status='approved')
                if Vote.objects.filter(user=user, position=position, candidate=candidate).exists():
                    return Response({'error': f'You already voted for {candidate.full_name}'}, status=status.HTTP_400_BAD_REQUEST)

                vote_hash = hashlib.sha256(
                    f"{user.uuid}{election.uuid}{position.uuid}{candidate.uuid}{timezone.now().isoformat()}".encode()
                ).hexdigest()
                from elections.models import VotingChannel
                web_channel = VotingChannel.objects.get(channel_name='web')
                vote = Vote.objects.create(
                    user=user,
                    election=election,
                    position=position,
                    candidate=candidate,
                    channel=web_channel,
                    svt=svt,
                    vote_hash=vote_hash
                )
                votes_created.append(vote)

        svt.status = 'used'
        svt.used_at = timezone.now()
        svt.save()

        confirmation_code = f"VTB-{str(election.uuid)[:4]}-{random.randint(100000, 999999)}"

        return Response({
            'message': 'Vote submitted successfully',
            'confirmation_code': confirmation_code,
            'votes': len(votes_created)
        })
