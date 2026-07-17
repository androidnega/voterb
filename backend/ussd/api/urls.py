from django.urls import path
from .views import (
    USSDSessionListView,
    USSDSessionDetailView,
    USSDRequestLogListView,
    USSDStatsView,
    USSDWebhookView,
)

urlpatterns = [
    path('callback/', USSDWebhookView.as_view(), name='ussd-callback'),
    path('sessions/', USSDSessionListView.as_view(), name='ussd-session-list'),
    path('sessions/<uuid:uuid>/', USSDSessionDetailView.as_view(), name='ussd-session-detail'),
    path('sessions/<uuid:session_uuid>/logs/', USSDRequestLogListView.as_view(), name='ussd-session-logs'),
    path('stats/', USSDStatsView.as_view(), name='ussd-stats'),
]
