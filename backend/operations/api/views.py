import os
import sys
import psutil
import time
from datetime import datetime, timedelta
from django.db import connections
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.core.cache import cache
import redis

from accounts.permissions import IsAdminOrSuperAdmin
from accounts.models import User, Session
from elections.models import Election
from voting.models import Vote
from notifications.models import InAppNotification
from strongroom.models import CustodyRecord

class HealthCheckView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }

        # Database check
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT 1")
            status['services']['database'] = 'healthy'
        except:
            status['services']['database'] = 'unhealthy'
            status['status'] = 'degraded'

        # Redis check
        try:
            r = redis.Redis.from_url('redis://localhost:6379/0')
            r.ping()
            status['services']['redis'] = 'healthy'
        except:
            status['services']['redis'] = 'unhealthy'
            status['status'] = 'degraded'

        # Cache check
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                status['services']['cache'] = 'healthy'
            else:
                status['services']['cache'] = 'unhealthy'
        except:
            status['services']['cache'] = 'unhealthy'

        return Response(status)

class InfrastructureMetricsView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()

        # Database connections (SQLite has no pool — report as N/A)
        try:
            db_connections = len(connections['default'].connection.pool._connections)
        except Exception:
            db_connections = 1 if connections['default'].connection else 0

        # Redis info
        try:
            r = redis.Redis.from_url('redis://localhost:6379/0')
            redis_info = r.info()
            redis_memory = redis_info.get('used_memory_human', 'N/A')
            redis_connected_clients = redis_info.get('connected_clients', 0)
        except:
            redis_memory = 'N/A'
            redis_connected_clients = 0

        return Response({
            'cpu': {
                'percent': cpu_percent,
                'cores': psutil.cpu_count()
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            },
            'database': {
                'connections': db_connections
            },
            'redis': {
                'memory': redis_memory,
                'clients': redis_connected_clients
            },
            'uptime': time.time() - psutil.boot_time()
        })

class QueueStatusView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        # For now, we'll use celery if available, otherwise simulate
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            active = inspect.active() if inspect else None
            scheduled = inspect.scheduled() if inspect else None
            reserved = inspect.reserved() if inspect else None

            return Response({
                'active_tasks': sum(len(v) for v in (active or {}).values()) if active else 0,
                'scheduled_tasks': sum(len(v) for v in (scheduled or {}).values()) if scheduled else 0,
                'reserved_tasks': sum(len(v) for v in (reserved or {}).values()) if reserved else 0,
                'celery_enabled': True
            })
        except:
            # Simulated queue status
            return Response({
                'active_tasks': 0,
                'scheduled_tasks': 0,
                'reserved_tasks': 0,
                'celery_enabled': False
            })

class SystemLogsView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        # Recent activity from various logs
        logs = []

        # Get recent MFALogs
        from accounts.models import MFALog
        mfa_logs = MFALog.objects.order_by('-created_at')[:10]
        for log in mfa_logs:
            logs.append({
                'level': 'info',
                'timestamp': log.created_at.isoformat(),
                'source': 'mfa',
                'message': f"{log.event_type} by {log.user.email if log.user else 'unknown'}",
                'details': f"IP: {log.ip_address or 'N/A'}"
            })

        # Get recent AuditLogs
        from security.models import AuditLog
        audit_logs = AuditLog.objects.order_by('-timestamp')[:10]
        for log in audit_logs:
            logs.append({
                'level': 'info',
                'timestamp': log.timestamp.isoformat(),
                'source': 'audit',
                'message': log.event_type,
                'details': f"User: {log.user.email if log.user else 'system'}"
            })

        # Sort by timestamp
        logs.sort(key=lambda x: x['timestamp'], reverse=True)

        return Response(logs[:50])

class OperationsOverviewView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        # Counts
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        total_elections = Election.objects.count()
        active_elections = Election.objects.filter(status='open').count()
        total_votes = Vote.objects.count()
        active_sessions = Session.objects.filter(is_active=True).count()
        pending_deliveries = InAppNotification.objects.filter(is_read=False).count()

        # Recent activity (last hour)
        hour_ago = timezone.now() - timedelta(hours=1)
        recent_votes = Vote.objects.filter(timestamp__gte=hour_ago).count()
        recent_logins = Session.objects.filter(created_at__gte=hour_ago).count()
        recent_errors = logs.filter(level='error').count() if False else 0  # placeholder

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
            'uptime': time.time() - psutil.boot_time()
        })
