import uuid
from django.db import models
from django.utils import timezone
from accounts.models import User
from elections.models import Election

class ElectionResult(models.Model):
    STATUS_CHOICES = [
        ('generated', 'Generated'),
        ('pending_certification', 'Pending Certification'),
        ('certified', 'Certified'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.OneToOneField(Election, on_delete=models.CASCADE, related_name='result')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='generated')
    standings = models.JSONField(default=dict)  # { positions: [{ title, candidates: [{ name, votes, percentage, rank }] }] }
    integrity_report = models.JSONField(default=dict)  # { vote_hash_verified: bool, svt_consistency: bool, duplicate_check: bool }
    result_hash = models.CharField(max_length=128, blank=True)  # SHA-256 of standings + metadata
    turnout_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    certified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='certified_results')
    certified_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Results for {self.election.title} ({self.status})"
