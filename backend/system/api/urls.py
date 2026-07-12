from django.urls import path
from .views import (
    FeatureFlagListView,
    FeatureFlagUpdateView,
    InstitutionProfileView,
    MaintenanceStateView,
    SystemSettingsByCategoryView,
    SystemSettingUpdateView,
)
from .theme_views import UIThemeView

urlpatterns = [
    path('feature-flags/', FeatureFlagListView.as_view(), name='feature-flag-list'),
    path('feature-flags/<str:key>/', FeatureFlagUpdateView.as_view(), name='feature-flag-update'),
    path('institution/', InstitutionProfileView.as_view(), name='institution-profile'),
    path('maintenance/', MaintenanceStateView.as_view(), name='maintenance-state'),
    path('theme/', UIThemeView.as_view(), name='ui-theme'),
    path('settings/', SystemSettingsByCategoryView.as_view(), name='settings-by-category'),
    path('settings/<str:key>/', SystemSettingUpdateView.as_view(), name='setting-update'),
]
