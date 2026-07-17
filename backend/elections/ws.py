"""Broadcast helpers for live election monitor WebSockets."""

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def broadcast_election_monitor(election):
    """Push a fresh monitor snapshot to all connected clients for this election."""
    if election is None:
        return
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    from elections.consumers import monitor_group_name
    from elections.monitor_service import get_election_monitor_data

    payload = get_election_monitor_data(election)
    async_to_sync(channel_layer.group_send)(
        monitor_group_name(str(election.uuid)),
        {
            'type': 'monitor.snapshot',
            'payload': payload,
        },
    )
