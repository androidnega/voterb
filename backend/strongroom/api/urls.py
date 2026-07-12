from django.urls import path
from .views import (
    StrongroomElectionListView,
    StrongroomElectionDetailView,
    LockElectionView,
    PublicVerifyView,
    VaultAuthenticateView,
    VaultSessionStatusView,
    VaultSessionCloseView,
    ElectionVaultAccessView,
    RevealSealView,
)

urlpatterns = [
    path('vault/authenticate/', VaultAuthenticateView.as_view(), name='vault-authenticate'),
    path('vault/session/status/', VaultSessionStatusView.as_view(), name='vault-session-status'),
    path('vault/session/close/', VaultSessionCloseView.as_view(), name='vault-session-close'),
    path('elections/', StrongroomElectionListView.as_view(), name='strongroom-election-list'),
    path('elections/<uuid:uuid>/', StrongroomElectionDetailView.as_view(), name='strongroom-election-detail'),
    path('elections/<uuid:uuid>/access/', ElectionVaultAccessView.as_view(), name='strongroom-election-access'),
    path('elections/<uuid:uuid>/reveal-seal/', RevealSealView.as_view(), name='strongroom-reveal-seal'),
    path('elections/<uuid:uuid>/lock/', LockElectionView.as_view(), name='strongroom-election-lock'),
    path('public/verify/', PublicVerifyView.as_view(), name='public-verify'),
]
