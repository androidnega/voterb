import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser


def monitor_group_name(election_uuid: str) -> str:
    return f'election_monitor_{election_uuid}'


class ElectionMonitorConsumer(AsyncWebsocketConsumer):
    """Live election monitor feed for EC/auditor clients."""

    async def connect(self):
        self.election_uuid = self.scope['url_route']['kwargs']['election_uuid']
        self.group = monitor_group_name(self.election_uuid)
        user = self.scope.get('user')

        if not user or isinstance(user, AnonymousUser) or not getattr(user, 'is_authenticated', False):
            await self.close(code=4401)
            return

        if not await self._can_view_monitor(user):
            await self.close(code=4403)
            return

        election = await self._get_election(self.election_uuid)
        if not election:
            await self.close(code=4404)
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

        snapshot = await self._build_snapshot(election)
        await self.send(text_data=json.dumps({
            'type': 'monitor.snapshot',
            'payload': snapshot,
        }))

    async def disconnect(self, code):
        if hasattr(self, 'group'):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            message = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if message.get('type') == 'monitor.refresh':
            election = await self._get_election(self.election_uuid)
            if not election:
                return
            snapshot = await self._build_snapshot(election)
            await self.send(text_data=json.dumps({
                'type': 'monitor.snapshot',
                'payload': snapshot,
            }))

    async def monitor_snapshot(self, event):
        """Channel-layer handler — push a fresh snapshot to this socket."""
        await self.send(text_data=json.dumps({
            'type': 'monitor.snapshot',
            'payload': event.get('payload') or {},
        }))

    @database_sync_to_async
    def _can_view_monitor(self, user):
        from accounts.permissions import get_role_name
        from accounts.org import user_is_main_ec, user_is_sub_ec
        role = get_role_name(user)
        if role in ('admin', 'sub_ec', 'auditor'):
            return True
        return user_is_main_ec(user) or user_is_sub_ec(user)

    @database_sync_to_async
    def _get_election(self, election_uuid):
        from elections.models import Election
        return Election.objects.filter(uuid=election_uuid).first()

    @database_sync_to_async
    def _build_snapshot(self, election):
        from elections.monitor_service import get_election_monitor_data
        return get_election_monitor_data(election)
