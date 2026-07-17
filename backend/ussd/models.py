import uuid

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from accounts.models import User
from elections.models import Election


class USSDSession(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
        ('error', 'Error'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider_session_id = models.CharField(max_length=64, blank=True, db_index=True)
    msisdn = models.CharField(max_length=20, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    election = models.ForeignKey(Election, on_delete=models.SET_NULL, null=True, blank=True)
    current_step = models.CharField(max_length=50, blank=True)
    state_data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Session {self.msisdn} - {self.status}'


class USSDRequestLog(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(USSDSession, on_delete=models.CASCADE, related_name='logs')
    request_payload = models.JSONField(default=dict)
    response_text = models.TextField(blank=True)
    outcome = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Log {self.uuid} - {self.session.msisdn}'


class USSDVoterPin(models.Model):
    """6-digit election PIN, hashed per voter per election (USSD channel)."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='ussd_pins')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ussd_pins')
    pin_hash = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('election', 'user')

    def __str__(self):
        return f'USSD PIN {self.user_id} / {self.election_id}'

    def set_pin(self, raw_pin: str):
        self.pin_hash = make_password(str(raw_pin).strip())

    def check_pin(self, raw_pin: str) -> bool:
        return check_password(str(raw_pin).strip(), self.pin_hash)
