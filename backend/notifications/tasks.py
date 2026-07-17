"""Celery tasks for outbound SMS and SMS prewarm."""

from __future__ import annotations

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name='notifications.send_sms',
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def send_sms_task(self, phone: str, message: str, cache_key: str | None = None) -> dict:
    from notifications.sms import send_sms

    result = send_sms(phone=phone, message=message, cache_key=cache_key)
    if not result.get('ok'):
        # Retry transient provider failures; permanent config errors should not loop forever.
        error = (result.get('error') or '').lower()
        permanent = any(
            token in error
            for token in ('api key missing', 'not configured', 'disabled', 'invalid phone')
        )
        if not permanent and self.request.retries < self.max_retries:
            raise self.retry(exc=RuntimeError(result.get('error') or 'SMS failed'))
    return result


@shared_task(name='notifications.send_svt_sms', max_retries=2, default_retry_delay=3)
def send_svt_sms_task(
    phone: str,
    code: str,
    election_title: str,
    election_uuid: str | None = None,
    user_uuid: str | None = None,
) -> dict:
    from notifications.sms import send_svt_sms

    return send_svt_sms(
        phone=phone,
        code=code,
        election_title=election_title,
        election_uuid=election_uuid,
        user_uuid=user_uuid,
    )


@shared_task(name='notifications.prewarm_election_sms')
def prewarm_election_sms_task(election_uuid: str, hours_ahead: int = 5) -> dict:
    from elections.models import Election
    from notifications.sms import prewarm_election_sms_payloads

    election = Election.objects.filter(uuid=election_uuid).first()
    if not election:
        return {'ok': False, 'error': 'Election not found'}
    stats = prewarm_election_sms_payloads(election, hours_ahead=hours_ahead)
    return {'ok': True, **stats}


def dispatch_sms(*, phone: str, message: str, cache_key: str | None = None, realtime: bool = True) -> dict:
    """
    Send SMS via Celery workers when available.

    realtime=True (OTP/SVT): wait briefly for the worker result so the user gets
    the code immediately; fall back to in-process send if workers/broker are down.
    realtime=False: fire-and-forget queue.
    """
    from django.conf import settings

    if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
        return send_sms_task(phone=phone, message=message, cache_key=cache_key)

    try:
        async_result = send_sms_task.apply_async(
            kwargs={'phone': phone, 'message': message, 'cache_key': cache_key},
            queue=getattr(settings, 'CELERY_TASK_DEFAULT_QUEUE', 'votebridge'),
        )
        if not realtime:
            return {
                'ok': True,
                'queued': True,
                'task_id': async_result.id,
                'masked_phone': None,
                'provider': 'celery',
            }
        # Keep OTP/login paths snappy; fall back to sync if workers are slow.
        result = async_result.get(timeout=5)
        if isinstance(result, dict):
            result['queued'] = True
            result['task_id'] = async_result.id
            return result
        return {'ok': True, 'queued': True, 'task_id': async_result.id, 'result': result}
    except Exception as exc:
        logger.warning('Celery SMS dispatch failed (%s) — sending in-process', exc)
        from notifications.sms import send_sms

        result = send_sms(phone=phone, message=message, cache_key=cache_key)
        result['celery_fallback'] = True
        return result


def dispatch_svt_sms(
    *,
    phone: str,
    code: str,
    election_title: str,
    election_uuid: str | None = None,
    user_uuid: str | None = None,
) -> dict:
    """Realtime SVT delivery through workers with sync fallback."""
    from django.conf import settings

    if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
        return send_svt_sms_task(
            phone=phone,
            code=code,
            election_title=election_title,
            election_uuid=election_uuid,
            user_uuid=user_uuid,
        )

    try:
        async_result = send_svt_sms_task.apply_async(
            kwargs={
                'phone': phone,
                'code': code,
                'election_title': election_title,
                'election_uuid': election_uuid,
                'user_uuid': user_uuid,
            },
            queue=getattr(settings, 'CELERY_TASK_DEFAULT_QUEUE', 'votebridge'),
        )
        result = async_result.get(timeout=20)
        if isinstance(result, dict):
            result['queued'] = True
            result['task_id'] = async_result.id
            return result
        return {'ok': bool(result), 'queued': True, 'task_id': async_result.id}
    except Exception as exc:
        logger.warning('Celery SVT SMS failed (%s) — sending in-process', exc)
        from notifications.sms import send_svt_sms

        result = send_svt_sms(
            phone=phone,
            code=code,
            election_title=election_title,
            election_uuid=election_uuid,
            user_uuid=user_uuid,
        )
        result['celery_fallback'] = True
        return result
