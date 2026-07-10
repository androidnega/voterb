from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.permissions import IsAdminOrSuperAdmin
from elections.models import Election
from strongroom.models import ElectionSeal, BallotSeal
from strongroom.serializers import StrongroomElectionDetailSerializer

# ----- List elections with strongroom data (admin) -----
class StrongroomElectionListView(generics.ListAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = StrongroomElectionDetailSerializer
    queryset = Election.objects.all().order_by('-created_at')

# ----- Detail view for a specific election's strongroom data -----
class StrongroomElectionDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = StrongroomElectionDetailSerializer
    lookup_field = 'uuid'
    queryset = Election.objects.all()

# ----- Lock an election (set it as locked for custody) -----
class LockElectionView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        # You may want to set a custom field 'is_locked' – but we can use status.
        # For simplicity, we'll just create a custody record.
        from strongroom.models import CustodyRecord
        CustodyRecord.objects.create(
            election=election,
            action='election_locked',
            actor=request.user,
            metadata={'timestamp': timezone.now().isoformat()}
        )
        return Response({'message': 'Election locked successfully'})

# ----- Public verification endpoint (no auth) -----
class PublicVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        seal_hash = request.data.get('seal_hash')
        if not seal_hash:
            return Response({'error': 'seal_hash required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if it's an ElectionSeal
        election_seal = ElectionSeal.objects.filter(seal_hash=seal_hash).first()
        if election_seal:
            return Response({
                'type': 'election_seal',
                'valid': True,
                'election': election_seal.election.title,
                'created_at': election_seal.created_at,
                'status': election_seal.status
            })

        # Check if it's a BallotSeal
        ballot_seal = BallotSeal.objects.filter(seal_hash=seal_hash).first()
        if ballot_seal:
            return Response({
                'type': 'ballot_seal',
                'valid': True,
                'election': ballot_seal.election.title,
                'created_at': ballot_seal.created_at,
                'status': ballot_seal.status
            })

        return Response({'valid': False, 'message': 'No matching seal found'})
