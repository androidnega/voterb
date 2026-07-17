from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from accounts.permissions import IsElectionViewer, IsMainECOrSubEC
from elections.models import Election
from elections.services.ec_access import (
    ElectionAccessBlocked,
    assert_can_manage_election,
    elections_visible_to,
)
from candidates.models import Candidate
from candidates.serializers import CandidateSerializer


def _election_for_viewer(request, election_uuid):
    return get_object_or_404(elections_visible_to(request.user), uuid=election_uuid)


def _manage_or_403(user, election):
    try:
        assert_can_manage_election(user, election)
        return None
    except ElectionAccessBlocked as exc:
        return Response(
            {'detail': str(exc), 'code': exc.code},
            status=status.HTTP_403_FORBIDDEN,
        )


def _locked_after_start(election):
    if election.status in ('open', 'paused', 'closed', 'archived'):
        return Response(
            {
                'detail': 'This election has started. Candidate changes are locked.',
                'code': 'election_locked',
            },
            status=status.HTTP_409_CONFLICT,
        )
    return None


class CandidateListCreateView(generics.ListCreateAPIView):
    """GET: election viewers. POST: Main/Sub EC who can manage the election."""
    serializer_class = CandidateSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsElectionViewer()]
        return [IsMainECOrSubEC()]

    def get_queryset(self):
        election = _election_for_viewer(self.request, self.kwargs['election_uuid'])
        return Candidate.objects.filter(election=election).order_by(
            'position__display_order', 'ballot_number'
        )

    def create(self, request, *args, **kwargs):
        election = _election_for_viewer(request, self.kwargs['election_uuid'])
        locked = _locked_after_start(election)
        if locked:
            return locked
        blocked = _manage_or_403(request.user, election)
        if blocked:
            return blocked
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        election = _election_for_viewer(self.request, self.kwargs['election_uuid'])
        serializer.save(election=election)


class CandidateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET: election viewers. Mutations: owning Main/Sub EC only."""
    serializer_class = CandidateSerializer
    lookup_field = 'uuid'
    lookup_url_kwarg = 'candidate_uuid'

    def get_permissions(self):
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [IsElectionViewer()]
        return [IsMainECOrSubEC()]

    def get_queryset(self):
        election = _election_for_viewer(self.request, self.kwargs['election_uuid'])
        return Candidate.objects.filter(election=election)

    def update(self, request, *args, **kwargs):
        election = _election_for_viewer(request, self.kwargs['election_uuid'])
        locked = _locked_after_start(election)
        if locked:
            return locked
        blocked = _manage_or_403(request.user, election)
        if blocked:
            return blocked
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        election = _election_for_viewer(request, self.kwargs['election_uuid'])
        locked = _locked_after_start(election)
        if locked:
            return locked
        blocked = _manage_or_403(request.user, election)
        if blocked:
            return blocked
        return super().destroy(request, *args, **kwargs)


class CandidateApproveView(APIView):
    permission_classes = [IsMainECOrSubEC]

    def post(self, request, election_uuid, candidate_uuid):
        election = _election_for_viewer(request, election_uuid)
        locked = _locked_after_start(election)
        if locked:
            return locked
        blocked = _manage_or_403(request.user, election)
        if blocked:
            return blocked
        candidate = get_object_or_404(Candidate, uuid=candidate_uuid, election=election)
        candidate.status = 'approved'
        candidate.save(update_fields=['status'])
        return Response({'message': 'Candidate approved'})


class CandidateRejectView(APIView):
    permission_classes = [IsMainECOrSubEC]

    def post(self, request, election_uuid, candidate_uuid):
        election = _election_for_viewer(request, election_uuid)
        locked = _locked_after_start(election)
        if locked:
            return locked
        blocked = _manage_or_403(request.user, election)
        if blocked:
            return blocked
        candidate = get_object_or_404(Candidate, uuid=candidate_uuid, election=election)
        candidate.status = 'rejected'
        candidate.save(update_fields=['status'])
        return Response({'message': 'Candidate rejected'})
