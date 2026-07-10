from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from accounts.models import User
from elections.models import Election, VoterEligibility
from elections.serializers import VoterEligibilitySerializer
from accounts.permissions import IsAdminOrSuperAdmin
import csv
import io

class EligibilityListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = VoterEligibilitySerializer

    def get_queryset(self):
        election_uuid = self.kwargs['election_uuid']
        election = get_object_or_404(Election, uuid=election_uuid)
        return VoterEligibility.objects.filter(election=election).select_related('user', 'verified_by')

    def perform_create(self, serializer):
        election_uuid = self.kwargs['election_uuid']
        election = get_object_or_404(Election, uuid=election_uuid)
        serializer.save(election=election, verified_by=self.request.user)

class EligibilityDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    lookup_field = 'uuid'

    def get_queryset(self):
        election_uuid = self.kwargs['election_uuid']
        election = get_object_or_404(Election, uuid=election_uuid)
        return VoterEligibility.objects.filter(election=election)

class EligibilityBulkImportView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

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
                identifier = row.get('identifier') or row.get('email') or row.get('index_number')
                if not identifier:
                    errors.append(f"Missing identifier in row: {row}")
                    continue

                user = User.objects.filter(email=identifier).first() or User.objects.filter(index_number=identifier).first()
                if not user:
                    errors.append(f"User not found for identifier: {identifier}")
                    continue

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
