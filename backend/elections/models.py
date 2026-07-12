import uuid
from django.db import models
from accounts.models import User


class Faculty(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'faculties'

    def __str__(self):
        return self.name


class Department(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.faculty.name})'


class Level(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=20, unique=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


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

    SCOPE_CHOICES = [
        ('school', 'School-wide'),
        ('faculty', 'Faculty'),
        ('department', 'Department'),
        ('level', 'Level'),
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
    scope_type = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='school')
    scope_faculty = models.ForeignKey(
        Faculty, on_delete=models.SET_NULL, null=True, blank=True, related_name='scoped_elections'
    )
    scope_department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='scoped_elections'
    )
    scope_level = models.ForeignKey(
        Level, on_delete=models.SET_NULL, null=True, blank=True, related_name='scoped_elections'
    )
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='elections_created')
    demo_seed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def user_matches_scope(self, user):
        """Return True if the student's academic profile matches this election's scope."""
        if self.scope_type == 'school':
            return True
        if self.scope_type == 'faculty':
            return bool(self.scope_faculty_id and user.faculty_id == self.scope_faculty_id)
        if self.scope_type == 'department':
            return bool(self.scope_department_id and user.department_id == self.scope_department_id)
        if self.scope_type == 'level':
            return bool(self.scope_level_id and user.level_id == self.scope_level_id)
        return False

    def get_scope_eligible_students(self):
        """Students matching this election's academic scope who completed onboarding."""
        qs = User.objects.filter(
            role__name='student',
            is_active=True,
            onboarding_completed=True,
        )
        if self.scope_type == 'faculty' and self.scope_faculty_id:
            return qs.filter(faculty_id=self.scope_faculty_id)
        if self.scope_type == 'department' and self.scope_department_id:
            return qs.filter(department_id=self.scope_department_id)
        if self.scope_type == 'level' and self.scope_level_id:
            return qs.filter(level_id=self.scope_level_id)
        return qs

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
