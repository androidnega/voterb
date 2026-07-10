from django.urls import path
from .views import (
    StrongroomElectionListView,
    StrongroomElectionDetailView,
    LockElectionView,
    PublicVerifyView,
)

urlpatterns = [
    path('elections/', StrongroomElectionListView.as_view(), name='strongroom-election-list'),
    path('elections/<uuid:uuid>/', StrongroomElectionDetailView.as_view(), name='strongroom-election-detail'),
    path('elections/<uuid:uuid>/lock/', LockElectionView.as_view(), name='strongroom-election-lock'),
    path('public/verify/', PublicVerifyView.as_view(), name='public-verify'),
]
