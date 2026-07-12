from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from accounts.models import User
from elections.models import Election, VoterEligibility
from elections.serializers import VoterEligibilitySerializer
from elections.services.eligibility import resolve_or_create_voter
from django.utils import timezone
from accounts.permissions import IsAdmin, IsElectionViewer
import csv
import io

class EligibilityListCreateView(generics.ListCreateAPIView):
    serializer_class = VoterEligibilitySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsElectionViewer()]
        return [IsAdmin()]

    def get_queryset(self):
        election_uuid = self.kwargs['election_uuid']
        election = get_object_or_404(Election, uuid=election_uuid)
        return VoterEligibility.objects.filter(election=election).select_related('user', 'verified_by')

    def perform_create(self, serializer):
        election_uuid = self.kwargs['election_uuid']
        election = get_object_or_404(Election, uuid=election_uuid)
        serializer.save(election=election, verified_by=self.request.user)

class EligibilityDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAdmin]
    lookup_field = 'uuid'

    def get_queryset(self):
        election_uuid = self.kwargs['election_uuid']
        election = get_object_or_404(Election, uuid=election_uuid)
        return VoterEligibility.objects.filter(election=election)

class EligibilityBulkImportView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, election_uuid):
        election = get_object_or_404(Election, uuid=election_uuid)
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Parse CSV
            decoded = file.read().decode('utf-8')
            io_string = io.StringIO(decoded)
            reader = csv.DictReader(io_string)
            created_count = 0
            errors = []

            for row in reader:
                index_number = (row.get('index_number') or row.get('identifier') or '').strip()
                if not index_number:
                    errors.append(f"Missing index_number in row: {row}")
                    continue

                if '@' in index_number:
                    errors.append(f"{index_number}: students use index numbers only, not email")
                    continue

                user, error_message = resolve_or_create_voter(index_number)

                if error_message or not user:
                    errors.append(f"{index_number}: {error_message or 'Student not found'}")
                    continue

                first_name = row.get('first_name', '').strip()
                last_name = row.get('last_name', '').strip()
                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
                if first_name or last_name:
                    user.save()

                # Check if already exists
                if VoterEligibility.objects.filter(election=election, user=user).exists():
                    continue

                VoterEligibility.objects.create(
                    election=election,
                    user=user,
                    is_eligible=True,
                    verified_by=request.user,
                    verified_at=timezone.now()
                )
                created_count += 1

            return Response({
                'created': created_count,
                'errors': errors
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
