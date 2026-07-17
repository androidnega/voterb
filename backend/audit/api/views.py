from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import MFALog
from accounts.permissions import IsAuditor
from security.models import AuditLog
from security.services.vote_audit import VOTER_AUDIT_EVENTS

from .serializers import (
    MFALogSerializer,
    VoteAuditListSerializer,
    VoteAuditDetailSerializer,
)


def _voter_audit_queryset():
    return (
        AuditLog.objects.filter(event_type__in=VOTER_AUDIT_EVENTS)
        .select_related('user', 'election', 'device_log', 'location_log')
        .order_by('-timestamp')
    )


def _apply_voter_audit_filters(qs, params):
    user_q = params.get('user')
    event = params.get('event') or params.get('event_type')
    election = params.get('election')
    if user_q:
        qs = qs.filter(
            Q(user__email__icontains=user_q)
            | Q(user__index_number__icontains=user_q)
            | Q(user__first_name__icontains=user_q)
            | Q(user__last_name__icontains=user_q)
            | Q(user__uuid__iexact=user_q)
        )
    if event:
        qs = qs.filter(event_type__icontains=event)
    if election:
        qs = qs.filter(election__uuid=election)
    return qs


class MFAHistoryView(generics.ListAPIView):
    """Legacy MFA trail — not shown in the voter audit UI."""

    permission_classes = [IsAuditor]
    serializer_class = MFALogSerializer
    queryset = MFALog.objects.all().order_by('-created_at')


class AuditHistoryView(generics.ListAPIView):
    """Normal vote-cast logs — no vault unlock required."""

    permission_classes = [IsAuditor]
    serializer_class = VoteAuditListSerializer

    def get_queryset(self):
        return _apply_voter_audit_filters(_voter_audit_queryset(), self.request.query_params)


class VoteAuditDetailView(APIView):
    """Full voter audit detail — device, location, presence photo. No ballot choices."""

    permission_classes = [IsAuditor]

    def get(self, request, audit_id):
        audit = _voter_audit_queryset().filter(audit_id=audit_id).first()
        if not audit:
            return Response({'error': 'Audit record not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(VoteAuditDetailSerializer(audit, context={'request': request}).data)


class CombinedAuditView(APIView):
    """
    Normal vote-cast audit logs for EC/auditor.
    Super Admin is excluded via IsAuditor. No vault unlock required.
    """

    permission_classes = [IsAuditor]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 100)), 500)
        qs = _apply_voter_audit_filters(_voter_audit_queryset(), request.query_params)
        data = VoteAuditListSerializer(qs[:limit], many=True, context={'request': request}).data
        return Response(data)
