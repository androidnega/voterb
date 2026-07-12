from django.urls import path
from .views import AdminDashboardView, SuperAdminDashboardView

urlpatterns = [
    path('admin/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('super-admin/', SuperAdminDashboardView.as_view(), name='super-admin-dashboard'),
]
