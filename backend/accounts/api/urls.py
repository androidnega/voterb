from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.api.governance_views import (
    GovernanceStatusView,
    MainECDecisionApproveView,
    MainECDecisionDetailView,
    MainECDecisionListView,
    MainECDecisionRejectView,
    MainECStructureUpdateView,
    MainECStructureView,
)
from .views import (
    LoginView, OTPVerifyView, OTPResendView, LogoutView, MeView,
    StudentOnboardingView, StudentOnboardingOptionsView,
    UserListView, UserDetailView,
    UserActivateView, UserDeactivateView, UserResetPasswordView,
    RoleListView
)

urlpatterns = [
    # ─── Authentication ──────────────────────────────────────
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/otp/verify/', OTPVerifyView.as_view(), name='otp-verify'),
    path('auth/otp/resend/', OTPResendView.as_view(), name='otp-resend'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', MeView.as_view(), name='me'),

    # ─── Student Onboarding ─────────────────────────────────
    path('onboarding/options/', StudentOnboardingOptionsView.as_view(), name='onboarding-options'),
    path('onboarding/', StudentOnboardingView.as_view(), name='onboarding'),

    # ─── User Management (Super Admin only) ─────────────────
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<uuid:uuid>/', UserDetailView.as_view(), name='user-detail'),
    path('users/<uuid:uuid>/activate/', UserActivateView.as_view(), name='user-activate'),
    path('users/<uuid:uuid>/deactivate/', UserDeactivateView.as_view(), name='user-deactivate'),
    path('users/<uuid:uuid>/reset-password/', UserResetPasswordView.as_view(), name='user-reset-password'),

    # ─── Roles (Super Admin only) ──────────────────────────
    path('roles/', RoleListView.as_view(), name='role-list'),

    # ─── Main EC dual-approval governance ───────────────────
    path('governance/status/', GovernanceStatusView.as_view(), name='governance-status'),
    path('governance/decisions/', MainECDecisionListView.as_view(), name='governance-decisions'),
    path('governance/decisions/<uuid:uuid>/', MainECDecisionDetailView.as_view(), name='governance-decision-detail'),
    path('governance/decisions/<uuid:uuid>/approve/', MainECDecisionApproveView.as_view(), name='governance-decision-approve'),
    path('governance/decisions/<uuid:uuid>/reject/', MainECDecisionRejectView.as_view(), name='governance-decision-reject'),
    path('governance/ec-structure/', MainECStructureView.as_view(), name='governance-ec-structure'),
    path(
        'governance/ec-structure/<uuid:unit_uuid>/',
        MainECStructureUpdateView.as_view(),
        name='governance-ec-structure-update',
    ),
]
