from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404

from elections.models import Election
from candidates.models import Candidate
from candidates.serializers import CandidateSerializer
from accounts.permissions import IsAdmin, IsElectionViewer


class CandidateListCreateView(generics.ListCreateAPIView):
    serializer_class = CandidateSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsElectionViewer()]
        return [IsAdmin()]

    def get_queryset(self):
        election_uuid = self.kwargs['election_uuid']
        election = get_object_or_404(Election, uuid=election_uuid)
        return Candidate.objects.filter(election=election).select_related(
            'position', 'faculty', 'academic_department'
        ).order_by('position__display_order', 'ballot_number')

    def perform_create(self, serializer):
        election = get_object_or_404(Election, uuid=self.kwargs['election_uuid'])
        serializer.save(election=election)


class CandidateDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CandidateSerializer
    lookup_field = 'uuid'
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsElectionViewer()]
        return [IsAdmin()]

    def get_queryset(self):
        election_uuid = self.kwargs['election_uuid']
        return Candidate.objects.filter(election__uuid=election_uuid).select_related(
            'position', 'faculty', 'academic_department'
        )


class CandidateApproveView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, election_uuid, candidate_uuid):
        candidate = get_object_or_404(Candidate, uuid=candidate_uuid, election__uuid=election_uuid)
        candidate.status = 'approved'
        candidate.save()
        return Response({'message': 'Candidate approved successfully'})


class CandidateRejectView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, election_uuid, candidate_uuid):
        candidate = get_object_or_404(Candidate, uuid=candidate_uuid, election__uuid=election_uuid)
        candidate.status = 'rejected'
        candidate.save()
        return Response({'message': 'Candidate rejected successfully'})
