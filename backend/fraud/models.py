import uuid
from django.db import models
from django.utils import timezone
from accounts.models import User
from elections.models import Election

class SecurityAlert(models.Model):
    ALERT_TYPES = [
        ('login_attempts', 'Excessive Login Attempts'),
        ('svt_requests', 'Excessive SVT Requests'),
        ('voting_pattern', 'Suspicious Voting Pattern'),
        ('duplicate_device', 'Duplicate Device Usage'),
        ('impossible_travel', 'Impossible Travel'),
        ('suspicious_activity', 'Suspicious Activity'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
        ('escalated', 'Escalated'),
    ]
    
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    election = models.ForeignKey(Election, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    metadata = models.JSONField(default=dict)
    detected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.alert_type} - {self.severity}"

class FraudCase(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
        ('escalated', 'Escalated'),
    ]
    
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert = models.OneToOneField(SecurityAlert, on_delete=models.CASCADE, related_name='fraud_case')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    severity = models.CharField(max_length=20, choices=SecurityAlert.SEVERITY_CHOICES, default='medium')
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    investigator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='investigated_cases')
    notes = models.JSONField(default=list)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"FraudCase {self.uuid[:8]} - {self.status}"
