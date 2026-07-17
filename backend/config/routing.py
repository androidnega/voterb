from django.urls import re_path

from elections.consumers import ElectionMonitorConsumer

websocket_urlpatterns = [
    re_path(
        r'^ws/elections/(?P<election_uuid>[0-9a-f-]+)/monitor/$',
        ElectionMonitorConsumer.as_asgi(),
    ),
]
