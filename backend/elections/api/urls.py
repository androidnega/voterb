from django.urls import path

from .views import (
    ElectionListCreateView, ElectionDetailView,
    PositionListCreateView,
    OpenElectionView, CloseElectionView, ElectionMonitorView
)
from .academic_views import (
    FacultyListCreateView, FacultyDetailView,
    DepartmentListCreateView, DepartmentDetailView,
    LevelListCreateView, LevelDetailView,
)
from .eligibility_views import EligibilityListCreateView, EligibilityDeleteView, EligibilityBulkImportView

urlpatterns = [
    path('faculties/', FacultyListCreateView.as_view(), name='faculty-list-create'),
    path('faculties/<uuid:uuid>/', FacultyDetailView.as_view(), name='faculty-detail'),
    path('departments/', DepartmentListCreateView.as_view(), name='department-list-create'),
    path('departments/<uuid:uuid>/', DepartmentDetailView.as_view(), name='department-detail'),
    path('levels/', LevelListCreateView.as_view(), name='level-list-create'),
    path('levels/<uuid:uuid>/', LevelDetailView.as_view(), name='level-detail'),
    path('', ElectionListCreateView.as_view(), name='election-list-create'),
    path('<uuid:uuid>/', ElectionDetailView.as_view(), name='election-detail'),
    path('<uuid:election_uuid>/positions/', PositionListCreateView.as_view(), name='position-list-create'),
    path('<uuid:uuid>/open/', OpenElectionView.as_view(), name='election-open'),
    path('<uuid:uuid>/close/', CloseElectionView.as_view(), name='election-close'),
    path('<uuid:uuid>/monitor/', ElectionMonitorView.as_view(), name='election-monitor'),
    path('<uuid:election_uuid>/eligibility/', EligibilityListCreateView.as_view(), name='eligibility-list-create'),
    path('<uuid:election_uuid>/eligibility/<uuid:uuid>/', EligibilityDeleteView.as_view(), name='eligibility-delete'),
    path('<uuid:election_uuid>/eligibility/import/', EligibilityBulkImportView.as_view(), name='eligibility-import'),
]
