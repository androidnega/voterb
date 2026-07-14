from django.urls import path

from .views import (
    MFAHistoryView,
    AuditHistoryView,
    CombinedAuditView,
    VoteAuditDetailView,
)

urlpatterns = [
    path('mfa/', MFAHistoryView.as_view(), name='mfa-history'),
    path('audit/', AuditHistoryView.as_view(), name='audit-history'),
    path('combined/', CombinedAuditView.as_view(), name='combined-audit'),
    path('<uuid:audit_id>/', VoteAuditDetailView.as_view(), name='vote-audit-detail'),
]
