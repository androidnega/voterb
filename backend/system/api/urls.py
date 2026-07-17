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
from .institution_views import (
    InstitutionListCreateView,
    InstitutionDetailView,
    InstitutionMainECCreateView,
    MyInstitutionsView,
)

urlpatterns = [
    path('feature-flags/', FeatureFlagListView.as_view(), name='feature-flag-list'),
    path('feature-flags/<str:key>/', FeatureFlagUpdateView.as_view(), name='feature-flag-update'),
    path('institution/', InstitutionProfileView.as_view(), name='institution-profile'),
    path('institutions/', InstitutionListCreateView.as_view(), name='institution-list'),
    path('institutions/mine/', MyInstitutionsView.as_view(), name='institution-mine'),
    path('institutions/<uuid:uuid>/', InstitutionDetailView.as_view(), name='institution-detail'),
    path(
        'institutions/<uuid:uuid>/main-ec/',
        InstitutionMainECCreateView.as_view(),
        name='institution-main-ec-create',
    ),
    path('maintenance/', MaintenanceStateView.as_view(), name='maintenance-state'),
    path('theme/', UIThemeView.as_view(), name='ui-theme'),
    path('settings/', SystemSettingsByCategoryView.as_view(), name='settings-by-category'),
    path('settings/<str:key>/', SystemSettingUpdateView.as_view(), name='setting-update'),
]
