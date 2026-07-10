from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

from accounts.permissions import IsAdminOrSuperAdmin
from ussd.models import USSDSession, USSDRequestLog
from ussd.serializers import USSDSessionSerializer, USSDRequestLogSerializer

class USSDSessionListView(generics.ListAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = USSDSessionSerializer
    queryset = USSDSession.objects.all().order_by('-created_at')

class USSDSessionDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = USSDSessionSerializer
    lookup_field = 'uuid'
    queryset = USSDSession.objects.all()

class USSDRequestLogListView(generics.ListAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = USSDRequestLogSerializer
    queryset = USSDRequestLog.objects.all().order_by('-timestamp')

    def get_queryset(self):
        session_uuid = self.kwargs.get('session_uuid')
        if session_uuid:
            session = get_object_or_404(USSDSession, uuid=session_uuid)
            return USSDRequestLog.objects.filter(session=session).order_by('-timestamp')
        return super().get_queryset()

class USSDStatsView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        total_sessions = USSDSession.objects.count()
        active_sessions = USSDSession.objects.filter(status='active').count()
        completed_sessions = USSDSession.objects.filter(status='completed').count()
        expired_sessions = USSDSession.objects.filter(status='expired').count()
        error_sessions = USSDSession.objects.filter(status='error').count()
        total_requests = USSDRequestLog.objects.count()
        # Last 24 hours
        yesterday = timezone.now() - timezone.timedelta(hours=24)
        recent_sessions = USSDSession.objects.filter(created_at__gte=yesterday).count()
        recent_requests = USSDRequestLog.objects.filter(timestamp__gte=yesterday).count()

        return Response({
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
            'expired_sessions': expired_sessions,
            'error_sessions': error_sessions,
            'total_requests': total_requests,
            'recent_sessions': recent_sessions,
            'recent_requests': recent_requests,
        })
