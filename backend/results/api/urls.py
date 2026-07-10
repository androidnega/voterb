from django.urls import path
from .views import (
    GenerateResultsView,
    PreviewResultsView,
    CertifyResultsView,
    PublishResultsView,
    ResultsListView,
    CertificationQueueView,
    PublishedResultsListView,
    PublishedResultDetailView,
)

urlpatterns = [
    path('elections/', ResultsListView.as_view(), name='results-list'),
    path('certification-queue/', CertificationQueueView.as_view(), name='certification-queue'),
    path('elections/<uuid:uuid>/generate/', GenerateResultsView.as_view(), name='results-generate'),
    path('elections/<uuid:uuid>/preview/', PreviewResultsView.as_view(), name='results-preview'),
    path('elections/<uuid:uuid>/certify/', CertifyResultsView.as_view(), name='results-certify'),
    path('elections/<uuid:uuid>/publish/', PublishResultsView.as_view(), name='results-publish'),
    path('published/', PublishedResultsListView.as_view(), name='published-results'),
    path('published/<uuid:uuid>/', PublishedResultDetailView.as_view(), name='published-result-detail'),
]
