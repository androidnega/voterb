from django.urls import path
from .views import (
    ElectionListCreateView, ElectionDetailView,
    PositionListCreateView, PositionDetailView,
    OpenElectionView, CloseElectionView, ElectionMonitorView
)
from .eligibility_views import EligibilityListCreateView, EligibilityDeleteView, EligibilityBulkImportView
from .academic_views import FacultyListView, DepartmentListView
from .academic_views import FacultyCreateView, DepartmentCreateView
from .academic_views import InstitutionCategoryListCreateView, InstitutionCategoryDetailView
from .register_views import (
    RegisterListCreateView,
    RegisterDetailView,
    CategoryListCreateView,
    CategoryDetailView,
    RegisterEntryListView,
    RegisterImportView,
    AvailableRegisterListView,
)
from .institution_register_views import (
    InstitutionRegisterListCreateView,
    InstitutionRegisterDetailView,
    InstitutionCategoryListCreateView as RegisterCategoryListCreateView,
    InstitutionCategoryDetailView as RegisterCategoryDetailView,
    InstitutionRegisterEntryListView,
    InstitutionRegisterEntryUpdateView,
    InstitutionRegisterImportView,
    InstitutionRegisterReplaceView,
)

urlpatterns = [
    # ─── ACADEMIC STRUCTURE (Main EC writes categories; anyone authenticated reads) ───
    path('faculties/', FacultyListView.as_view(), name='faculty-list'),
    path('faculties/create/', FacultyCreateView.as_view(), name='faculty-create'),
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('departments/create/', DepartmentCreateView.as_view(), name='department-create'),
    path(
        'institution-categories/',
        InstitutionCategoryListCreateView.as_view(),
        name='institution-category-list',
    ),
    path(
        'institution-categories/<uuid:uuid>/',
        InstitutionCategoryDetailView.as_view(),
        name='institution-category-detail',
    ),

    # ─── INSTITUTIONAL REGISTERS (Main EC) ───────────────────────
    path('institution-registers/', InstitutionRegisterListCreateView.as_view(), name='institution-register-list'),
    path(
        'institution-registers/<uuid:register_uuid>/',
        InstitutionRegisterDetailView.as_view(),
        name='institution-register-detail',
    ),
    path(
        'institution-registers/<uuid:register_uuid>/categories/',
        RegisterCategoryListCreateView.as_view(),
        name='institution-register-categories',
    ),
    path(
        'institution-registers/<uuid:register_uuid>/categories/<uuid:category_uuid>/',
        RegisterCategoryDetailView.as_view(),
        name='institution-register-category-detail',
    ),
    path(
        'institution-registers/<uuid:register_uuid>/entries/',
        InstitutionRegisterEntryListView.as_view(),
        name='institution-register-entries',
    ),
    path(
        'institution-registers/<uuid:register_uuid>/entries/<uuid:entry_uuid>/',
        InstitutionRegisterEntryUpdateView.as_view(),
        name='institution-register-entry-update',
    ),
    path(
        'institution-registers/<uuid:register_uuid>/import/',
        InstitutionRegisterImportView.as_view(),
        name='institution-register-import',
    ),
    path(
        'institution-registers/<uuid:register_uuid>/replace/',
        InstitutionRegisterReplaceView.as_view(),
        name='institution-register-replace',
    ),

    # ─── ELECTIONS (Admin only) ──────────────────────────────────
    path('', ElectionListCreateView.as_view(), name='election-list-create'),
    path('registers/available/', AvailableRegisterListView.as_view(), name='register-available-list'),
    path('<uuid:uuid>/', ElectionDetailView.as_view(), name='election-detail'),
    path('<uuid:uuid>/positions/', PositionListCreateView.as_view(), name='position-list-create'),
    path(
        '<uuid:uuid>/positions/<uuid:position_uuid>/',
        PositionDetailView.as_view(),
        name='position-detail',
    ),
    path('<uuid:uuid>/open/', OpenElectionView.as_view(), name='election-open'),
    path('<uuid:uuid>/close/', CloseElectionView.as_view(), name='election-close'),
    path('<uuid:uuid>/monitor/', ElectionMonitorView.as_view(), name='election-monitor'),

    # ─── VOTER REGISTERS ─────────────────────────────────────────
    path('<uuid:election_uuid>/registers/', RegisterListCreateView.as_view(), name='register-list-create'),
    path(
        '<uuid:election_uuid>/registers/<uuid:register_uuid>/',
        RegisterDetailView.as_view(),
        name='register-detail',
    ),
    path(
        '<uuid:election_uuid>/registers/<uuid:register_uuid>/categories/',
        CategoryListCreateView.as_view(),
        name='register-category-list-create',
    ),
    path(
        '<uuid:election_uuid>/registers/<uuid:register_uuid>/categories/<uuid:category_uuid>/',
        CategoryDetailView.as_view(),
        name='register-category-detail',
    ),
    path(
        '<uuid:election_uuid>/registers/<uuid:register_uuid>/entries/',
        RegisterEntryListView.as_view(),
        name='register-entry-list',
    ),
    path(
        '<uuid:election_uuid>/registers/<uuid:register_uuid>/import/',
        RegisterImportView.as_view(),
        name='register-import',
    ),

    # ─── ELIGIBILITY (derived from registers; legacy table kept in sync) ──
    path('<uuid:election_uuid>/eligibility/', EligibilityListCreateView.as_view(), name='eligibility-list-create'),
    path('<uuid:election_uuid>/eligibility/<uuid:uuid>/', EligibilityDeleteView.as_view(), name='eligibility-delete'),
    path('<uuid:election_uuid>/eligibility/import/', EligibilityBulkImportView.as_view(), name='eligibility-import'),
]
