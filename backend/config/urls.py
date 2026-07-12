from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/accounts/', include('accounts.api.urls')),
    path('api/v1/elections/', include('elections.api.urls')),
    path('api/v1/elections/<uuid:election_uuid>/candidates/', include('candidates.api.urls')),
    path('api/v1/voting/', include('voting.api.urls')),
    path('api/v1/results/', include('results.api.urls')),
    path('api/v1/strongroom/', include('strongroom.api.urls')),
    path('api/v1/fraud/', include('fraud.api.urls')),
    path('api/v1/notifications/', include('notifications.api.urls')),
    path('api/v1/system/', include('system.api.urls')),
    path('api/v1/dashboard/', include('dashboard.api.urls')),
    path('api/v1/ussd/', include('ussd.api.urls')),
    path('api/v1/audit/', include('audit.api.urls')),
    path('api/v1/operations/', include('operations.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
