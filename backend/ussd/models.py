import uuid
from django.db import models
from accounts.models import User
from elections.models import Election

class USSDSession(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    msisdn = models.CharField(max_length=20, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    election = models.ForeignKey(Election, on_delete=models.SET_NULL, null=True, blank=True)
    current_step = models.CharField(max_length=50, blank=True)
    state_data = models.JSONField(default=dict)
    status = models.CharField(max_length=20, default='active')  # active, completed, expired, error
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.msisdn} - {self.status}"

class USSDRequestLog(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(USSDSession, on_delete=models.CASCADE, related_name='logs')
    request_payload = models.JSONField(default=dict)
    response_text = models.TextField(blank=True)
    outcome = models.CharField(max_length=20, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log {self.uuid} - {self.session.msisdn}"
