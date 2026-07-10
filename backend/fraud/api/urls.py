from django.urls import path
from .views import (
    AlertListView, AlertDetailView, AlertResolveView, AlertEscalateView,
    CaseListView, CaseDetailView, CaseAddNoteView, CaseResolveView,
    FraudDashboardStatsView
)

urlpatterns = [
    path('alerts/', AlertListView.as_view(), name='alert-list'),
    path('alerts/<uuid:uuid>/', AlertDetailView.as_view(), name='alert-detail'),
    path('alerts/<uuid:uuid>/resolve/', AlertResolveView.as_view(), name='alert-resolve'),
    path('alerts/<uuid:uuid>/escalate/', AlertEscalateView.as_view(), name='alert-escalate'),
    path('cases/', CaseListView.as_view(), name='case-list'),
    path('cases/<uuid:uuid>/', CaseDetailView.as_view(), name='case-detail'),
    path('cases/<uuid:uuid>/note/', CaseAddNoteView.as_view(), name='case-add-note'),
    path('cases/<uuid:uuid>/resolve/', CaseResolveView.as_view(), name='case-resolve'),
    path('stats/', FraudDashboardStatsView.as_view(), name='fraud-stats'),
]
