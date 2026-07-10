from django.urls import path
from candidates.api.views import (
    CandidateListCreateView, CandidateDetailView,
    CandidateApproveView, CandidateRejectView
)

urlpatterns = [
    path('', CandidateListCreateView.as_view(), name='candidate-list-create'),
    path('<uuid:candidate_uuid>/', CandidateDetailView.as_view(), name='candidate-detail'),
    path('<uuid:candidate_uuid>/approve/', CandidateApproveView.as_view(), name='candidate-approve'),
    path('<uuid:candidate_uuid>/reject/', CandidateRejectView.as_view(), name='candidate-reject'),
]
