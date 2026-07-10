import uuid
from django.db import models
from django.utils import timezone
from accounts.models import User

class Election(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('open', 'Open'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    
    TYPE_CHOICES = [
        ('general', 'General'),
        ('student_union', 'Student Union'),
        ('faculty', 'Faculty'),
        ('departmental', 'Departmental'),
        ('special', 'Special'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    election_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='general')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    allow_web_voting = models.BooleanField(default=True)
    allow_ussd_voting = models.BooleanField(default=False)
    allow_sms_notifications = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='elections_created')
    demo_seed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Position(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    max_votes_allowed = models.SmallIntegerField(default=1)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_votable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('election', 'title')
    
    def __str__(self):
        return f"{self.title} ({self.election.title})"

class VoterEligibility(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='eligibilities')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_eligible = models.BooleanField(default=True)
    eligibility_reason = models.TextField(blank=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_eligibilities')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('election', 'user')
    
    def __str__(self):
        return f"{self.user.email} - {self.election.title} ({'Eligible' if self.is_eligible else 'Not Eligible'})"

class VotingChannel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel_name = models.CharField(max_length=20, unique=True)  # web, ussd, sms
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.channel_name
