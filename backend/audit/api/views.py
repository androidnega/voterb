from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import MFALog
from accounts.permissions import IsAdminOrSuperAdmin
from security.models import AuditLog

from .serializers import MFALogSerializer, AuditLogSerializer


class MFAHistoryView(generics.ListAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = MFALogSerializer
    queryset = MFALog.objects.all().order_by('-created_at')


class AuditHistoryView(generics.ListAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all().order_by('-timestamp')


class CombinedAuditView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        user_uuid = request.query_params.get('user')
        event_type = request.query_params.get('event')
        limit = int(request.query_params.get('limit', 50))

        mfa_logs = MFALog.objects.all()
        audit_logs = AuditLog.objects.all()

        if user_uuid:
            mfa_logs = mfa_logs.filter(user__uuid=user_uuid)
            audit_logs = audit_logs.filter(user__uuid=user_uuid)
        if event_type:
            mfa_logs = mfa_logs.filter(event_type__icontains=event_type)
            audit_logs = audit_logs.filter(event_type__icontains=event_type)

        mfa_serializer = MFALogSerializer(mfa_logs[:limit], many=True)
        audit_serializer = AuditLogSerializer(audit_logs[:limit], many=True)

        combined = list(mfa_serializer.data) + list(audit_serializer.data)
        combined.sort(
            key=lambda x: x.get('created_at') or x.get('timestamp'),
            reverse=True,
        )

        return Response(combined[:limit])
