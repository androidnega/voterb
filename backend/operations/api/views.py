import time
from datetime import datetime, timedelta

import redis
from django.conf import settings
from django.core.cache import cache
from django.db import connections
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Session, User
from accounts.permissions import IsAdminOrSuperAdmin
from elections.models import Election
from notifications.models import InAppNotification
from system.settings_utils import get_setting, get_setting_bool
from voting.models import Vote

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


def _redis_url() -> str:
    return (
        (getattr(settings, 'REDIS_URL', None) or '').strip()
        or (getattr(settings, 'CELERY_BROKER_URL', None) or '').strip()
        or 'redis://127.0.0.1:6379/0'
    )


def _redis_client():
    return redis.Redis.from_url(_redis_url(), socket_connect_timeout=2, socket_timeout=2)


class HealthCheckView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        status_payload = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'redis_url_configured': bool(getattr(settings, 'REDIS_URL', '')),
        }

        try:
            with connections['default'].cursor() as cursor:
                cursor.execute('SELECT 1')
            status_payload['services']['database'] = 'healthy'
        except Exception:
            status_payload['services']['database'] = 'unhealthy'
            status_payload['status'] = 'degraded'

        try:
            r = _redis_client()
            r.ping()
            status_payload['services']['redis'] = 'healthy'
        except Exception:
            status_payload['services']['redis'] = 'unhealthy'
            status_payload['status'] = 'degraded'

        try:
            cache.set('health_check', 'ok', 10)
            status_payload['services']['cache'] = 'healthy' if cache.get('health_check') == 'ok' else 'unhealthy'
        except Exception:
            status_payload['services']['cache'] = 'unhealthy'

        try:
            from config.celery import app as celery_app
            inspector = celery_app.control.inspect(timeout=1.0)
            ping = inspector.ping() if inspector else None
            workers = list((ping or {}).keys())
            status_payload['services']['celery'] = 'healthy' if workers else 'unhealthy'
            status_payload['celery_workers'] = workers
            if not workers:
                status_payload['status'] = 'degraded'
        except Exception:
            status_payload['services']['celery'] = 'unhealthy'
            status_payload['celery_workers'] = []
            status_payload['status'] = 'degraded'

        sms_enabled = get_setting_bool('sms_enabled', True)
        has_key = bool(
            (get_setting('sms_arkesel_api_key') or get_setting('sms_api_key') or '').strip()
            or (get_setting('sms_moolre_api_key') or '').strip()
        )
        status_payload['services']['sms'] = 'healthy' if (sms_enabled and has_key) else 'unhealthy'
        if status_payload['services']['sms'] != 'healthy':
            status_payload['status'] = 'degraded'

        status_payload['services']['ussd'] = (
            'healthy' if get_setting_bool('ussd_enabled', True) else 'unhealthy'
        )

        return Response(status_payload)


class InfrastructureMetricsView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        cpu_percent = psutil.cpu_percent(interval=0.5) if psutil else 0
        memory = psutil.virtual_memory() if psutil else None

        try:
            db_connections = 1 if connections['default'].connection else 0
        except Exception:
            db_connections = 0

        try:
            r = _redis_client()
            redis_info = r.info()
            redis_memory = redis_info.get('used_memory_human', 'N/A')
            redis_connected_clients = redis_info.get('connected_clients', 0)
        except Exception:
            redis_memory = 'N/A'
            redis_connected_clients = 0

        return Response({
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count() if psutil else 0,
            },
            'memory': {
                'total': memory.total if memory else 0,
                'available': memory.available if memory else 0,
                'percent': memory.percent if memory else 0,
            },
            'database': {
                'connections': db_connections,
            },
            'redis': {
                'memory': redis_memory,
                'clients': redis_connected_clients,
                'url': _redis_url().split('@')[-1],
            },
            'uptime': (time.time() - psutil.boot_time()) if psutil else 0,
        })


class QueueStatusView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        try:
            from config.celery import app as celery_app

            inspector = celery_app.control.inspect(timeout=1.5)
            active = inspector.active() if inspector else None
            scheduled = inspector.scheduled() if inspector else None
            reserved = inspector.reserved() if inspector else None
            stats = inspector.stats() if inspector else None
            ping = inspector.ping() if inspector else None

            workers = list((ping or {}).keys())
            concurrency = 0
            if stats:
                for worker_stats in stats.values():
                    pool = worker_stats.get('pool') or {}
                    concurrency += int(pool.get('max-concurrency') or pool.get('processes') or 0)

            return Response({
                'celery_enabled': True,
                'workers': workers,
                'worker_count': len(workers),
                'concurrency': concurrency,
                'active_tasks': sum(len(v) for v in (active or {}).values()) if active else 0,
                'scheduled_tasks': sum(len(v) for v in (scheduled or {}).values()) if scheduled else 0,
                'reserved_tasks': sum(len(v) for v in (reserved or {}).values()) if reserved else 0,
                'broker': (getattr(settings, 'CELERY_BROKER_URL', '') or '').split('@')[-1],
                'queue': getattr(settings, 'CELERY_TASK_DEFAULT_QUEUE', 'votebridge'),
            })
        except Exception as exc:
            return Response({
                'celery_enabled': False,
                'workers': [],
                'worker_count': 0,
                'concurrency': 0,
                'active_tasks': 0,
                'scheduled_tasks': 0,
                'reserved_tasks': 0,
                'error': str(exc),
            })


class SystemLogsView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        logs = []

        from accounts.models import MFALog
        for log in MFALog.objects.order_by('-created_at')[:10]:
            logs.append({
                'level': 'info',
                'timestamp': log.created_at.isoformat(),
                'source': 'mfa',
                'message': f'{log.event_type} by {log.user.email if log.user else "unknown"}',
                'details': f'IP: {log.ip_address or "N/A"}',
            })

        from security.models import AuditLog
        for log in AuditLog.objects.order_by('-timestamp')[:10]:
            logs.append({
                'level': 'info',
                'timestamp': log.timestamp.isoformat(),
                'source': 'audit',
                'message': log.event_type,
                'details': f'User: {log.user.email if log.user else "system"}',
            })

        logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return Response(logs[:50])


class OperationsOverviewView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        total_elections = Election.objects.count()
        active_elections = Election.objects.filter(status='open').count()
        total_votes = Vote.objects.count()
        active_sessions = Session.objects.filter(is_active=True).count()
        pending_deliveries = InAppNotification.objects.filter(is_read=False).count()

        hour_ago = timezone.now() - timedelta(hours=1)
        recent_votes = Vote.objects.filter(timestamp__gte=hour_ago).count()
        recent_logins = Session.objects.filter(created_at__gte=hour_ago).count()

        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'total_elections': total_elections,
            'active_elections': active_elections,
            'total_votes': total_votes,
            'active_sessions': active_sessions,
            'pending_deliveries': pending_deliveries,
            'recent_votes': recent_votes,
            'recent_logins': recent_logins,
            'recent_errors': 0,
            'uptime': (time.time() - psutil.boot_time()) if psutil else 0,
        })
