import uuid
from django.db import models
from django.utils import timezone
from accounts.models import User
from elections.models import Election

# ---------- Existing Models ----------
class BallotSeal(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='ballot_seals')
    svt_id = models.UUIDField(null=True, blank=True)
    seal_hash = models.CharField(max_length=128)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BallotSeal {self.seal_hash[:16]}... ({self.election.title})"


class VoteCastEvidence(models.Model):
    """
    Strongroom custody record for a cast ballot's integrity evidence.
    Stores device/IP/location/fingerprint/presence references — never ballot choices.
    """
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='vote_cast_evidence')
    ballot_seal = models.OneToOneField(
        BallotSeal,
        on_delete=models.CASCADE,
        related_name='vote_evidence',
    )
    confirmation_code_hash = models.CharField(max_length=128, db_index=True)
    channel = models.CharField(max_length=20, default='web')
    audit_log_id = models.UUIDField(null=True, blank=True, db_index=True)
    presence_capture_id = models.UUIDField(null=True, blank=True, db_index=True)
    device_log_id = models.UUIDField(null=True, blank=True)
    location_log_id = models.UUIDField(null=True, blank=True)
    device_id = models.CharField(max_length=64, blank=True)
    browser_fingerprint = models.CharField(max_length=128, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    presence_image_path = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['election', 'created_at']),
            models.Index(fields=['election', 'confirmation_code_hash']),
        ]

    def __str__(self):
        return f"VoteEvidence {self.uuid} ({self.channel})"

class ElectionSeal(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.OneToOneField(Election, on_delete=models.CASCADE, related_name='election_seal')
    seal_hash = models.CharField(max_length=128)
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ElectionSeal {self.seal_hash[:16]}... ({self.election.title})"

class CustodyRecord(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='custody_records', null=True, blank=True)
    action = models.CharField(max_length=50)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        title = self.election.title if self.election else 'System'
        return f"{self.action} - {title}"

class IntegrityVerification(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='integrity_verifications')
    verification_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20)
    report = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.verification_type} - {self.election.title}"

# ---------- New Models for Committee & Vault ----------
class StrongroomCommittee(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='committees')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    nominated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='nominated_committees')
    peer_ec = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='peer_committees',
        help_text='Second EC who must approve this custody committee.',
    )
    peer_approved_at = models.DateTimeField(null=True, blank=True)
    peer_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_committees',
    )
    nominee_full_name = models.CharField(max_length=255, blank=True)
    nominee_phone = models.CharField(max_length=32, blank=True)
    nominee_email = models.EmailField(blank=True)
    nominee_key_hash = models.CharField(max_length=128, blank=True)
    nominee_key_expires_at = models.DateTimeField(null=True, blank=True)
    nominee_key_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Committee for {self.election.title} ({self.status})"

class StrongroomCommitteeMember(models.Model):
    ROLE_CHOICES = [
        ('chair', 'Chair'),
        ('custodian', 'Custodian'),
        ('observer', 'Observer'),
        ('main_ec', 'Main EC'),
        ('peer_ec', 'Peer EC'),
        ('nominee', 'Candidate Nominee'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    committee = models.ForeignKey(StrongroomCommittee, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='custodian')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('committee', 'user')

    def __str__(self):
        return f"{self.user.email} ({self.role})"

class VaultAccessRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='vault_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vault_requests')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_vault_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Vault Request for {self.election.title} ({self.status})"

class VaultSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    access_request = models.ForeignKey(VaultAccessRequest, on_delete=models.CASCADE, related_name='vault_sessions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    opened_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opened_vault_sessions')
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    evidence_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Vault Session for {self.access_request.election.title} ({self.status})"

class VaultEvidence(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(VaultSession, on_delete=models.CASCADE, related_name='evidence')
    seal_type = models.CharField(max_length=20)  # 'ballot' or 'election'
    seal_hash = models.CharField(max_length=128)
    seal_uuid = models.UUIDField()
    viewed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence {self.seal_hash[:16]}... viewed by {self.viewed_by.email}"


class StrongroomAccessSession(models.Model):
    """Step-up authenticated vault gate session for strongroom access."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strongroom_sessions')
    token_hash = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Strongroom session for {self.user.email}"


class VaultUnlockChallenge(models.Model):
    """
    Three-party unlock for the vote audit vault:
    1) initiating EC password
    2) peer EC confirm
    3) nominee hashed key
    """
    STATUS_CHOICES = [
        ('awaiting_peer', 'Awaiting peer EC'),
        ('awaiting_nominee', 'Awaiting nominee key'),
        ('open', 'Open'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='vault_unlock_challenges',
        null=True,
        blank=True,
    )
    committee = models.ForeignKey(
        StrongroomCommittee,
        on_delete=models.CASCADE,
        related_name='unlock_challenges',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='awaiting_peer')
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vault_unlocks_started')
    peer_confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vault_unlocks_confirmed',
    )
    peer_confirmed_at = models.DateTimeField(null=True, blank=True)
    nominee_verified_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    access_session = models.ForeignKey(
        StrongroomAccessSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unlock_challenges',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['committee', 'status']),
        ]

    def __str__(self):
        return f"VaultUnlock {self.uuid} ({self.status})"
