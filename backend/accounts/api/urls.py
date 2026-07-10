from django.urls import path
from .views import (
    LoginView, OTPVerifyView, LogoutView, MeView,
    UserListView, UserDetailView,
    UserActivateView, UserDeactivateView, UserResetPasswordView,
    RoleListView
)

urlpatterns = [
    # Authentication
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/me/', MeView.as_view(), name='me'),

    # User Management
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<uuid:uuid>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<uuid:uuid>/activate/', UserActivateView.as_view(), name='user-activate'),
    path('users/<uuid:uuid>/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'),
    path('users/<uuid:uuid>/reset-password/', UserResetPasswordView.as_view(), name='user-reset-password'),

    # Role Management
    path('roles/', RoleListView.as_view(), name='role-list'),
]
