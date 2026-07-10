from django.urls import path
from .views import (
    HealthCheckView,
    InfrastructureMetricsView,
    QueueStatusView,
    SystemLogsView,
    OperationsOverviewView
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='ops-health'),
    path('infrastructure/', InfrastructureMetricsView.as_view(), name='ops-infrastructure'),
    path('queues/', QueueStatusView.as_view(), name='ops-queues'),
    path('logs/', SystemLogsView.as_view(), name='ops-logs'),
    path('overview/', OperationsOverviewView.as_view(), name='ops-overview'),
]
