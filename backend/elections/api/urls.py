from django.urls import path
from .views import (
    ElectionListCreateView, ElectionDetailView,
    PositionListCreateView,
    OpenElectionView, CloseElectionView
)
from .eligibility_views import EligibilityListCreateView, EligibilityDeleteView, EligibilityBulkImportView

urlpatterns = [
    path('', ElectionListCreateView.as_view(), name='election-list-create'),
    path('<uuid:uuid>/', ElectionDetailView.as_view(), name='election-detail'),
    path('<uuid:election_uuid>/positions/', PositionListCreateView.as_view(), name='position-list-create'),
    path('<uuid:uuid>/open/', OpenElectionView.as_view(), name='election-open'),
    path('<uuid:uuid>/close/', CloseElectionView.as_view(), name='election-close'),
    path('<uuid:election_uuid>/eligibility/', EligibilityListCreateView.as_view(), name='eligibility-list-create'),
    path('<uuid:election_uuid>/eligibility/<uuid:uuid>/', EligibilityDeleteView.as_view(), name='eligibility-delete'),
    path('<uuid:election_uuid>/eligibility/import/', EligibilityBulkImportView.as_view(), name='eligibility-import'),
]
