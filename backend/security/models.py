import uuid
from django.db import models
from accounts.models import User
from elections.models import Election

class SVTToken(models.Model):
    svt_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    election = models.ForeignKey(Election, on_delete=models.PROTECT)
    token_hash = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=20, default='issued')  # issued,validated,used,expired,revoked
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    validated_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    validation_attempts = models.SmallIntegerField(default=0)
    last_resent_at = models.DateTimeField(null=True, blank=True)

class AuditLog(models.Model):
    audit_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    election = models.ForeignKey(Election, on_delete=models.SET_NULL, null=True)
    device_log = models.ForeignKey('DeviceLog', on_delete=models.SET_NULL, null=True)
    location_log = models.ForeignKey('LocationLog', on_delete=models.SET_NULL, null=True)
    event_type = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

class DeviceLog(models.Model):
    device_log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    browser_fingerprint = models.CharField(max_length=128)
    device_type = models.CharField(max_length=20, blank=True)
    operating_system = models.CharField(max_length=50, blank=True)
    user_agent = models.TextField(blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)

class LocationLog(models.Model):
    location_log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ip_address = models.GenericIPAddressField(unique=True)
    country = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_seen_at = models.DateTimeField(auto_now=True)
