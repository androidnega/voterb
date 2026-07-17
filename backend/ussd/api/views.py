from django.core.cache import cache
from django.http import JsonResponse
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
    Arkesel USSD callback (official Ghana API).
    POST /api/v1/ussd/callback/

    Request (JSON):
      sessionID, userID, newSession, msisdn, userData, network

    Response (JSON):
      sessionID, userID, msisdn, message, continueSession

    See: https://developers.arkesel.com/ (USSD) and
    https://github.com/ArkeselDev/express-ussd-sample

    Optional: when `ussd_api_key` is set, require X-API-Key.
    Leave blank for Arkesel — they do not send a webhook key.
    """

    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request):
        payload = self._flatten_payload(request.data)
        if request.query_params:
            payload = {**self._flatten_payload(request.query_params), **payload}

        safe_payload = {}
        for key, value in payload.items():
            safe_payload[str(key)] = (
                value if isinstance(value, (str, int, float, bool, type(None))) else str(value)
            )

        # Canonical Arkesel fields (+ Africa's Talking aliases for local tests).
        session_id = (
            safe_payload.get('sessionID')
            or safe_payload.get('sessionId')
            or safe_payload.get('session_id')
            or ''
        )
        user_id = (
            safe_payload.get('userID')
            or safe_payload.get('userId')
            or safe_payload.get('user_id')
            or ''
        )
        user_data = safe_payload.get('userData')
        if user_data is None:
            user_data = safe_payload.get('text')
        if user_data is None:
            user_data = safe_payload.get('message')
        if user_data is None:
            user_data = ''

        msisdn = normalize_msisdn(
            safe_payload.get('msisdn')
            or safe_payload.get('phoneNumber')
            or safe_payload.get('phone_number')
            or safe_payload.get('mobile')
            or ''
        ) or (
            safe_payload.get('msisdn')
            or safe_payload.get('phoneNumber')
            or safe_payload.get('phone_number')
            or ''
        )

        safe_payload['sessionID'] = str(session_id).strip()
        safe_payload['sessionId'] = safe_payload['sessionID']
        safe_payload['userID'] = str(user_id).strip()
        safe_payload['arkesel_user_id'] = safe_payload['userID']
        safe_payload['userData'] = user_data
        safe_payload['text'] = user_data
        safe_payload['msisdn'] = msisdn
        safe_payload.setdefault(
            'serviceCode',
            safe_payload.get('service_code') or safe_payload.get('shortCode') or '',
        )

        if not self._api_key_ok(request):
            return self._arkesel_json(
                session_id=safe_payload['sessionID'],
                user_id=safe_payload['userID'],
                msisdn=msisdn,
                message='Unauthorized',
                continue_session=False,
                status=401,
            )

        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        gateway_ip = (
            forwarded.split(',')[0].strip()
            if forwarded
            else request.META.get('REMOTE_ADDR')
        )
        if gateway_ip:
            safe_payload['_gateway_ip'] = gateway_ip

        if self._rate_limited(msisdn or 'unknown'):
            return self._arkesel_json(
                session_id=safe_payload['sessionID'],
                user_id=safe_payload['userID'],
                msisdn=msisdn,
                message='Too many requests. Please try again shortly.',
                continue_session=False,
                status=429,
            )

        result = process_ussd_request(safe_payload)
        message, continue_session = self._split_flow_response(result.response)

        USSDRequestLog.objects.create(
            session=result.session,
            request_payload=safe_payload,
            response_text=result.response,
            outcome=result.outcome,
        )
        return self._arkesel_json(
            session_id=safe_payload['sessionID'],
            user_id=safe_payload['userID'],
            msisdn=msisdn or getattr(result.session, 'msisdn', '') or '',
            message=message,
            continue_session=continue_session,
        )

    def get(self, request):
        """Health / discovery for gateway configuration checks."""
        return Response({
            'service': 'ussd',
            'provider': 'arkesel',
            'callback': '/api/v1/ussd/callback/',
            'method': 'POST',
            'request': 'application/json sessionID,userID,newSession,msisdn,userData,network',
            'response': 'application/json sessionID,userID,msisdn,message,continueSession',
            'auth': 'none (leave ussd_api_key blank for Arkesel)',
        })

    @staticmethod
    def _split_flow_response(flow_response: str) -> tuple[str, bool]:
        text = (flow_response or '').strip()
        if text.startswith('CON '):
            return text[4:].strip(), True
        if text.startswith('END '):
            return text[4:].strip(), False
        # Already plain menu text — keep session open unless empty.
        return text, bool(text)

    @staticmethod
    def _arkesel_json(*, session_id, user_id, msisdn, message, continue_session, status=200):
        return JsonResponse(
            {
                'sessionID': session_id or '',
                'userID': user_id or '',
                'msisdn': msisdn or '',
                'message': message or '',
                'continueSession': bool(continue_session),
            },
            status=status,
        )

    def _flatten_payload(self, data) -> dict:
        flattened = {}
        if data is None:
            return flattened
        for key in data.keys():
            values = data.getlist(key) if hasattr(data, 'getlist') else [data.get(key)]
            flattened[key] = values[-1] if values else ''
        return flattened

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
