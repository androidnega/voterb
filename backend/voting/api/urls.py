from django.urls import path
from .views import (
    EligibleElectionsView,
    SVTRequestView,
    SVTValidateView,
    SVTSessionView,
    PresenceCaptureView,
    BallotView,
    SubmitVoteView,
    ClearStudentVoteView,
)

urlpatterns = [
    path('eligible/', EligibleElectionsView.as_view(), name='eligible-elections'),
    path('elections/<uuid:uuid>/svt/request/', SVTRequestView.as_view(), name='svt-request'),
    path('elections/<uuid:uuid>/svt/validate/', SVTValidateView.as_view(), name='svt-validate'),
    path('elections/<uuid:uuid>/svt/session/', SVTSessionView.as_view(), name='svt-session'),
    path('elections/<uuid:uuid>/presence/', PresenceCaptureView.as_view(), name='presence-capture'),
    path('elections/<uuid:uuid>/ballot/', BallotView.as_view(), name='ballot'),
    path('elections/<uuid:uuid>/submit/', SubmitVoteView.as_view(), name='submit-vote'),
    path(
        'elections/<uuid:uuid>/voters/<uuid:user_uuid>/clear/',
        ClearStudentVoteView.as_view(),
        name='clear-student-vote',
    ),
]
