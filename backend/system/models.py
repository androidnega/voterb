import uuid
from django.db import models
from django.utils import timezone
from accounts.models import User

class InstitutionProfile(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, default='VoterB')
    short_name = models.CharField(max_length=50, default='VoterB')
    logo = models.ImageField(upload_to='institution/', blank=True, null=True)
    primary_color = models.CharField(max_length=7, default='#1e5f46')
    secondary_color = models.CharField(max_length=7, default='#0f7d3e')
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class SystemSetting(models.Model):
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('security', 'Security'),
        ('integrations', 'Integrations'),
        ('governance', 'Governance'),
        ('operations', 'Operations'),
    ]
    
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='general')
    description = models.TextField(blank=True)
    is_encrypted = models.BooleanField(default=False)  # For API keys and secrets
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key} = {self.value[:30] if not self.is_encrypted else '***'}"

class FeatureFlag(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True)
    is_enabled = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default='general')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key}: {self.is_enabled}"

class SettingRevision(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    setting_key = models.CharField(max_length=100)
    old_value = models.TextField()
    new_value = models.TextField()
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.setting_key} changed at {self.changed_at}"

class MaintenanceState(models.Model):
    is_active = models.BooleanField(default=False)
    message = models.TextField(blank=True, default='The system is currently under maintenance. Please check back later.')
    scheduled_start = models.DateTimeField(null=True, blank=True)
    scheduled_end = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Maintenance: {'Active' if self.is_active else 'Inactive'}"
