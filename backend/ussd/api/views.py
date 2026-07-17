from django.core.cache import cache
from django.db.models import Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from accounts.permissions import IsAdmin
from system.settings_utils import get_setting, get_setting_int
from ussd.models import USSDSession, USSDRequestLog
from ussd.serializers import USSDSessionSerializer, USSDRequestLogSerializer
from ussd.services.ussd_auth import normalize_msisdn
from ussd.services.ussd_flow import process_ussd_request


class USSDWebhookView(APIView):
    """
    Arkesel USSD callback.
    POST /api/v1/ussd/callback/

    Accepts JSON or form fields (sessionId/msisdn/text or sessionID/userData).
    Responds with plain-text CON/END menus.

    Auth: when `ussd_api_key` is set, require matching
    X-API-Key / api-key / Authorization: Bearer header.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        if not self._api_key_ok(request):
            return HttpResponse('END Unauthorized', content_type='text/plain', status=401)

        payload = dict(request.data) if request.data is not None else {}
        safe_payload = {}
        for key, value in payload.items():
            safe_payload[str(key)] = value if isinstance(value, (str, int, float, bool, type(None))) else str(value)

        msisdn = normalize_msisdn(
            safe_payload.get('msisdn')
            or safe_payload.get('phoneNumber')
            or safe_payload.get('phone_number')
            or ''
        )
        if msisdn:
            safe_payload['msisdn'] = msisdn

        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        gateway_ip = (
            forwarded.split(',')[0].strip()
            if forwarded
            else request.META.get('REMOTE_ADDR')
        )
        if gateway_ip:
            safe_payload['_gateway_ip'] = gateway_ip

        if self._rate_limited(msisdn or 'unknown'):
            body = 'END Too many requests. Please try again shortly.'
            return HttpResponse(body, content_type='text/plain', status=429)

        result = process_ussd_request(safe_payload)
        USSDRequestLog.objects.create(
            session=result.session,
            request_payload=safe_payload,
            response_text=result.response,
            outcome=result.outcome,
        )
        return HttpResponse(result.response, content_type='text/plain')

    def get(self, request):
        """Health / discovery for gateway configuration checks."""
        return Response({
            'service': 'ussd',
            'callback': '/api/v1/ussd/callback/',
            'method': 'POST',
            'response': 'text/plain CON|END',
            'auth': 'X-API-Key when ussd_api_key is configured',
        })

    def _api_key_ok(self, request) -> bool:
        expected = (get_setting('ussd_api_key') or '').strip()
        if not expected:
            return True
        provided = (
            request.headers.get('X-API-Key')
            or request.headers.get('Api-Key')
            or request.META.get('HTTP_X_API_KEY')
            or ''
        ).strip()
        if not provided:
            auth = (request.headers.get('Authorization') or '').strip()
            if auth.lower().startswith('bearer '):
                provided = auth[7:].strip()
        return bool(provided) and provided == expected

    def _rate_limited(self, msisdn: str) -> bool:
        limit = max(1, get_setting_int('ussd_rate_limit_per_minute', 10))
        window = 60
        key = f'ussd:rl:{msisdn}:{timezone.now().strftime("%Y%m%d%H%M")}'
        try:
            count = cache.get(key, 0)
            if count >= limit:
                return True
            cache.set(key, count + 1, timeout=window)
        except Exception:
            return False
        return False


class USSDSessionListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = USSDSessionSerializer
    queryset = USSDSession.objects.all().order_by('-created_at')


class USSDSessionDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdmin]
    serializer_class = USSDSessionSerializer
    lookup_field = 'uuid'
    queryset = USSDSession.objects.all()


class USSDRequestLogListView(generics.ListAPIView):
    permission_classes = [IsAdmin]
    serializer_class = USSDRequestLogSerializer
    queryset = USSDRequestLog.objects.all().order_by('-timestamp')

    def get_queryset(self):
        session_uuid = self.kwargs.get('session_uuid')
        if session_uuid:
            session = get_object_or_404(USSDSession, uuid=session_uuid)
            return USSDRequestLog.objects.filter(session=session).order_by('-timestamp')
        return super().get_queryset()


class USSDStatsView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        total_sessions = USSDSession.objects.count()
        active_sessions = USSDSession.objects.filter(status='active').count()
        completed_sessions = USSDSession.objects.filter(status='completed').count()
        expired_sessions = USSDSession.objects.filter(status='expired').count()
        error_sessions = USSDSession.objects.filter(status='error').count()
        total_requests = USSDRequestLog.objects.count()
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
