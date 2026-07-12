from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils import timezone

from accounts.permissions import IsAdmin
from fraud.models import SecurityAlert, FraudCase
from fraud.serializers import SecurityAlertSerializer, FraudCaseSerializer

class AlertListView(generics.ListCreateAPIView):
    permission_classes = [IsAdmin]
    serializer_class = SecurityAlertSerializer
    queryset = SecurityAlert.objects.all().order_by('-detected_at')

class AlertDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdmin]
    serializer_class = SecurityAlertSerializer
    lookup_field = 'uuid'
    queryset = SecurityAlert.objects.all()

class AlertResolveView(APIView):
    permission_classes = [IsAdmin]
    
    def post(self, request, uuid):
        alert = get_object_or_404(SecurityAlert, uuid=uuid)
        alert.status = 'resolved'
        alert.save()
        return Response({'message': 'Alert resolved'})

class AlertEscalateView(APIView):
    permission_classes = [IsAdmin]
    
    def post(self, request, uuid):
        alert = get_object_or_404(SecurityAlert, uuid=uuid)
        alert.status = 'escalated'
        alert.save()
        case = FraudCase.objects.create(alert=alert, status='open')
        return Response({'message': 'Alert escalated to fraud case', 'case_uuid': case.uuid})

class CaseListView(generics.ListCreateAPIView):
    permission_classes = [IsAdmin]
    serializer_class = FraudCaseSerializer
    queryset = FraudCase.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(investigator=self.request.user)

class CaseDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdmin]
    serializer_class = FraudCaseSerializer
    lookup_field = 'uuid'
    queryset = FraudCase.objects.all()

class CaseAddNoteView(APIView):
    permission_classes = [IsAdmin]
    
    def post(self, request, uuid):
        case = get_object_or_404(FraudCase, uuid=uuid)
        note = request.data.get('note')
        if not note:
            return Response({'error': 'Note is required'}, status=status.HTTP_400_BAD_REQUEST)
        notes = case.notes or []
        notes.append({
            'note': note,
            'timestamp': timezone.now().isoformat(),
            'author': request.user.email
        })
        case.notes = notes
        case.save()
        return Response({'message': 'Note added'})

class CaseResolveView(APIView):
    permission_classes = [IsAdmin]
    
    def post(self, request, uuid):
        case = get_object_or_404(FraudCase, uuid=uuid)
        case.status = 'resolved'
        case.resolved_at = timezone.now()
        case.save()
        case.alert.status = 'resolved'
        case.alert.save()
        return Response({'message': 'Case resolved'})

class FraudDashboardStatsView(APIView):
    permission_classes = [IsAdmin]
    
    def get(self, request):
        total_alerts = SecurityAlert.objects.count()
        open_alerts = SecurityAlert.objects.filter(status='open').count()
        high_risk = SecurityAlert.objects.filter(severity__in=['high', 'critical']).count()
        total_cases = FraudCase.objects.count()
        open_cases = FraudCase.objects.filter(status='open').count()
        recent_alerts = SecurityAlert.objects.filter(detected_at__gte=timezone.now() - timezone.timedelta(days=7)).count()
        
        return Response({
            'total_alerts': total_alerts,
            'open_alerts': open_alerts,
            'high_risk': high_risk,
            'total_cases': total_cases,
            'open_cases': open_cases,
            'recent_alerts': recent_alerts,
        })
