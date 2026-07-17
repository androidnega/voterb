import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class Role(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, email=None, password=None, **extra_fields):
        # For students, email is optional
        if not email and not extra_fields.get('index_number'):
            raise ValueError('Either email or index_number is required')
        if email:
            email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(unique=True, null=True, blank=True)  # Now optional
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    index_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    student_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # Now optional
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True)
    institution = models.ForeignKey(
        'system.InstitutionProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
    )
    faculty = models.ForeignKey('elections.Faculty', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey('elections.Department', on_delete=models.SET_NULL, null=True, blank=True)
    programme = models.CharField(max_length=100, blank=True, null=True)
    onboarding_completed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    demo_seed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email or self.index_number or str(self.uuid)


class ECUnit(models.Model):
    """Electoral Commission unit under an institution (Main EC or Sub EC)."""

    UNIT_MAIN = 'main'
    UNIT_SUB = 'sub'
    UNIT_CHOICES = [
        (UNIT_MAIN, 'Main EC'),
        (UNIT_SUB, 'Sub EC'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        'system.InstitutionProfile',
        on_delete=models.CASCADE,
        related_name='ec_units',
    )
    unit_type = models.CharField(max_length=10, choices=UNIT_CHOICES)
    name = models.CharField(max_length=150)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['unit_type', 'name']
        unique_together = ('institution', 'name')

    def __str__(self):
        return f'{self.name} ({self.get_unit_type_display()})'


class ECMembership(models.Model):
    """Links a user to an EC unit (Main or Sub)."""

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ec_memberships')
    ec_unit = models.ForeignKey(ECUnit, on_delete=models.CASCADE, related_name='memberships')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'ec_unit')
        ordering = ['ec_unit__name', 'user__email']

    def __str__(self):
        return f'{self.user} → {self.ec_unit.name}'


class SubECAssignment(models.Model):
    """
    Scopes a Sub EC unit to one or more faculties / departments.

    Phase A scaffold — filtering enforced in Phase C.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ec_unit = models.ForeignKey(
        ECUnit,
        on_delete=models.CASCADE,
        related_name='assignments',
        limit_choices_to={'unit_type': ECUnit.UNIT_SUB},
    )
    faculty = models.ForeignKey(
        'elections.Faculty',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_ec_assignments',
    )
    department = models.ForeignKey(
        'elections.Department',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_ec_assignments',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(faculty__isnull=False) | models.Q(department__isnull=False),
                name='sub_ec_assignment_has_scope',
            ),
        ]

    def __str__(self):
        scope = self.department or self.faculty
        return f'{self.ec_unit.name} → {scope}'


class MainECDecision(models.Model):
    """Institutional EC decision awaiting dual Main EC approval before enrollment."""

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_ENROLLED = 'enrolled'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_ENROLLED, 'Enrolled'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    TYPE_ELECTION_CREATE = 'election_create'
    TYPE_ELECTION_UPDATE = 'election_update'
    TYPE_ELECTION_OPEN = 'election_open'
    TYPE_ELECTION_CLOSE = 'election_close'
    TYPE_ELECTION_DELETE = 'election_delete'
    TYPE_SUB_EC_CREATE = 'sub_ec_create'
    TYPE_SUB_EC_UPDATE = 'sub_ec_update'
    TYPE_REGISTER_CREATE = 'register_create'
    TYPE_REGISTER_REPLACE = 'register_replace'
    TYPE_REGISTER_ENTRY_UPDATE = 'register_entry_update'
    TYPE_CHOICES = [
        (TYPE_ELECTION_CREATE, 'Create election'),
        (TYPE_ELECTION_UPDATE, 'Update election'),
        (TYPE_ELECTION_OPEN, 'Open election'),
        (TYPE_ELECTION_CLOSE, 'Close election'),
        (TYPE_ELECTION_DELETE, 'Delete election'),
        (TYPE_SUB_EC_CREATE, 'Create Sub EC'),
        (TYPE_SUB_EC_UPDATE, 'Update Sub EC'),
        (TYPE_REGISTER_CREATE, 'Create voter register'),
        (TYPE_REGISTER_REPLACE, 'Replace voter register'),
        (TYPE_REGISTER_ENTRY_UPDATE, 'Update voter register entry'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        'system.InstitutionProfile',
        on_delete=models.CASCADE,
        related_name='main_ec_decisions',
    )
    decision_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    proposed_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='proposed_ec_decisions',
    )
    result_ref = models.CharField(max_length=64, blank=True)
    enrolled_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rejected_ec_decisions',
    )
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.status})'


class MainECDecisionApproval(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    decision = models.ForeignKey(
        MainECDecision, on_delete=models.CASCADE, related_name='approvals',
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ec_decision_approvals')
    approved_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('decision', 'user')

    def __str__(self):
        return f'{self.user} approved {self.decision_id}'


class OTPRequest(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=20, choices=[('login', 'Login'), ('mfa', 'MFA')])
    channel = models.CharField(max_length=10, choices=[('sms', 'SMS'), ('email', 'Email')])
    otp_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.SmallIntegerField(default=0)
    max_attempts = models.SmallIntegerField(default=5)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Session(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    refresh_token_jti = models.CharField(max_length=64, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField()
    last_activity_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)


class MFALog(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    event_type = models.CharField(max_length=30)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
