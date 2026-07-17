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


class InstitutionCategory(models.Model):
    """
    Main EC institution-wide category (e.g. Institution, General, SRC).

    Created under Categories, then selected when building a Main EC register.
    Distinct from faculty/department categories used by Sub ECs.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        'system.InstitutionProfile',
        on_delete=models.CASCADE,
        related_name='institution_categories',
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'institution categories'
        constraints = [
            models.UniqueConstraint(
                fields=['institution', 'name'],
                name='uniq_institutioncategory_institution_name',
            ),
        ]

    def __str__(self):
        return f'{self.name} ({self.institution.short_name})'


class Election(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('open', 'Open'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]

    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    allow_web_voting = models.BooleanField(default=True)
    allow_ussd_voting = models.BooleanField(default=False)
    allow_sms_notifications = models.BooleanField(default=False)
    # Primary voter list for this election. The older election.registers
    # relation is retained so existing register-management screens and data
    # keep working during the transition to register-owned election scope.
    register = models.ForeignKey(
        'VoterRegister',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_elections',
    )

    # Who owns / manages this election
    OWNER_MAIN = 'main'
    OWNER_SUB = 'sub'
    OWNER_CHOICES = [
        (OWNER_MAIN, 'Main EC (institutional)'),
        (OWNER_SUB, 'Sub EC (category)'),
    ]
    owner_type = models.CharField(
        max_length=10,
        choices=OWNER_CHOICES,
        default=OWNER_MAIN,
        db_index=True,
    )
    institution = models.ForeignKey(
        'system.InstitutionProfile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='elections',
    )
    owner_ec_unit = models.ForeignKey(
        'accounts.ECUnit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_elections',
    )

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='elections_created')
    demo_seed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_main_owned(self) -> bool:
        return self.owner_type == self.OWNER_MAIN

    @property
    def is_sub_owned(self) -> bool:
        return self.owner_type == self.OWNER_SUB

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
    allow_all_voters = models.BooleanField(default=True)
    restricted_categories = models.ManyToManyField(
        'VoterCategory',
        blank=True,
        related_name='restricted_positions',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('election', 'title')

    def __str__(self):
        return f"{self.title} ({self.election.title})"

    def voter_may_see(self, user) -> bool:
        """
        True if this position should appear on the voter's ballot.
        allow_all_voters=True → every eligible voter sees it.
        Otherwise the voter must have a register entry in one of restricted_categories.
        """
        if self.allow_all_voters:
            return True
        if not user or not getattr(user, 'pk', None):
            return False
        category_ids = list(self.restricted_categories.values_list('pk', flat=True))
        if not category_ids:
            # Restricted but no categories selected → nobody sees it
            return False
        from elections.models import VoterRegisterEntry
        qs = VoterRegisterEntry.objects.filter(user=user, category_id__in=category_ids)
        if self.election.register_id:
            qs = qs.filter(register_id=self.election.register_id)
        else:
            qs = qs.filter(register__election_id=self.election_id)
        return qs.exists()

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


class VoterRegister(models.Model):
    """
    Institutional voter register (e.g. TTU Register).

    Main EC creates the register and assigns Categories (faculty / department)
    as voter containers. Elections may link via Election.register.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        'system.InstitutionProfile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='voter_registers',
    )
    # Legacy: older rows were owned by an election. Prefer institution going forward.
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='registers',
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # Who this register is for when creating elections.
    # Main EC institutional elections use AUDIENCE_MAIN (custom/institution categories).
    # Sub EC elections use AUDIENCE_SUB (faculty/department categories).
    AUDIENCE_MAIN = 'main'
    AUDIENCE_SUB = 'sub'
    AUDIENCE_CHOICES = [
        (AUDIENCE_MAIN, 'Main EC (institution-wide)'),
        (AUDIENCE_SUB, 'Sub EC (faculty / department)'),
    ]
    audience = models.CharField(
        max_length=10,
        choices=AUDIENCE_CHOICES,
        default=AUDIENCE_SUB,
        db_index=True,
    )

    # Dual Main EC approval — a second Main EC member must approve before the
    # register can be used for elections.
    APPROVAL_PENDING = 'pending'
    APPROVAL_APPROVED = 'approved'
    APPROVAL_REJECTED = 'rejected'
    APPROVAL_CHOICES = [
        (APPROVAL_PENDING, 'Pending approval'),
        (APPROVAL_APPROVED, 'Approved'),
        (APPROVAL_REJECTED, 'Rejected'),
    ]
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default=APPROVAL_APPROVED,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Staging register for dual-approved voter re-upload (points at the live register).
    replace_of = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='pending_replacements',
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registers_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_approved(self) -> bool:
        return self.approval_status == self.APPROVAL_APPROVED

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['institution', 'name'],
                condition=models.Q(institution__isnull=False),
                name='uniq_voterregister_institution_name',
            ),
            models.UniqueConstraint(
                fields=['election', 'name'],
                condition=models.Q(election__isnull=False),
                name='uniq_voterregister_election_name',
            ),
        ]

    def __str__(self):
        owner = self.institution.short_name if self.institution_id else (
            self.election.title if self.election_id else 'orphan'
        )
        return f'{self.name} ({owner})'


class VoterCategory(models.Model):
    """
    Category under a register — typically a faculty or department container
    that holds that unit's voters (e.g. Hospitality Voters, Comp. Sci. Voters).
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    register = models.ForeignKey(VoterRegister, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='register_categories',
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='register_categories',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('register', 'name')
        verbose_name_plural = 'voter categories'
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(faculty__isnull=True) | models.Q(department__isnull=True)
                ),
                name='voter_category_not_both_faculty_and_department',
            ),
        ]

    def __str__(self):
        return f'{self.name} · {self.register.name}'

    @property
    def category_type(self):
        if self.department_id:
            return 'department'
        if self.faculty_id:
            return 'faculty'
        return 'custom'

    @property
    def scope_label(self):
        if self.department_id:
            return f'Department · {self.department.name}'
        if self.faculty_id:
            return f'Faculty · {self.faculty.name}'
        return f'Main EC · {self.name}'

class VoterRegisterEntry(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    register = models.ForeignKey(VoterRegister, on_delete=models.CASCADE, related_name='entries')
    category = models.ForeignKey(
        VoterCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='entries'
    )
    voter_id = models.CharField(max_length=50)
    full_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='register_entries'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('register', 'voter_id')
        verbose_name_plural = 'voter register entries'

    def __str__(self):
        return f'{self.voter_id} — {self.full_name}'


class VoterRegisterImport(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    register = models.ForeignKey(VoterRegister, on_delete=models.CASCADE, related_name='imports')
    file_name = models.CharField(max_length=255)
    rows_processed = models.IntegerField(default=0)
    rows_created = models.IntegerField(default=0)
    errors = models.JSONField(default=list, blank=True)
    imported_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='voter_register_imports'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Import {self.file_name} → {self.register.name}'
