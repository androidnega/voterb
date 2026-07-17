"""JWT authentication for Django Channels WebSockets."""

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def _user_from_token(token: str):
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    from rest_framework_simplejwt.tokens import AccessToken
    from accounts.models import User

    try:
        access = AccessToken(token)
        user_id = access.get('user_uuid') or access.get('user_id')
        if not user_id:
            return AnonymousUser()
        user = (
            User.objects.select_related('role')
            .filter(uuid=user_id, is_active=True)
            .first()
        )
        return user or AnonymousUser()
    except (InvalidToken, TokenError, Exception):
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    """
    Authenticate WS connections via ?token=<jwt> query string
    (browsers cannot set Authorization headers on WebSocket).
    """

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get('query_string', b'').decode())
        raw = (query.get('token') or [None])[0]
        if raw:
            scope['user'] = await _user_from_token(raw)
        else:
            scope['user'] = AnonymousUser()
        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(inner)
