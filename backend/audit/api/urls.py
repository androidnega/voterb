from django.urls import path
from .views import MFAHistoryView, AuditHistoryView, CombinedAuditView

urlpatterns = [
    path('mfa/', MFAHistoryView.as_view(), name='mfa-history'),
    path('audit/', AuditHistoryView.as_view(), name='audit-history'),
    path('combined/', CombinedAuditView.as_view(), name='combined-audit'),
]
