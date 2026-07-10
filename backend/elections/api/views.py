from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from elections.models import Election, Position
from elections.serializers import ElectionSerializer, ElectionCreateUpdateSerializer, PositionSerializer
from candidates.models import Candidate
from accounts.permissions import IsAdminOrSuperAdmin

# Election Views
class ElectionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    queryset = Election.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ElectionCreateUpdateSerializer
        return ElectionSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class ElectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    queryset = Election.objects.all()
    lookup_field = 'uuid'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ElectionCreateUpdateSerializer
        return ElectionSerializer

# Position Views
class PositionListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = PositionSerializer
    
    def get_queryset(self):
        election_uuid = self.kwargs['election_uuid']
        election = get_object_or_404(Election, uuid=election_uuid)
        return Position.objects.filter(election=election).order_by('display_order')
    
    def perform_create(self, serializer):
        election = get_object_or_404(Election, uuid=self.kwargs['election_uuid'])
        serializer.save(election=election)

# Action Views
class OpenElectionView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    
    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        if election.status != 'scheduled':
            return Response({'error': 'Election must be scheduled before opening'}, status=status.HTTP_400_BAD_REQUEST)
        election.status = 'open'
        election.save()
        return Response({'message': 'Election opened successfully'})

class CloseElectionView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]
    
    def post(self, request, uuid):
        election = get_object_or_404(Election, uuid=uuid)
        if election.status != 'open' and election.status != 'paused':
            return Response({'error': 'Election must be open or paused to close'}, status=status.HTTP_400_BAD_REQUEST)
        election.status = 'closed'
        election.save()
        return Response({'message': 'Election closed successfully'})
