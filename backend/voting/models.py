import uuid
from django.db import models
from elections.models import Election, Position, VotingChannel
from candidates.models import Candidate
from accounts.models import User
from security.models import SVTToken

class Vote(models.Model):
    vote_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    election = models.ForeignKey(Election, on_delete=models.PROTECT)
    position = models.ForeignKey(Position, on_delete=models.PROTECT)
    candidate = models.ForeignKey(Candidate, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    channel = models.ForeignKey(VotingChannel, on_delete=models.PROTECT)
    svt = models.ForeignKey(SVTToken, on_delete=models.PROTECT, null=True)
    vote_hash = models.CharField(max_length=128)  # SHA-256
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'position', 'candidate')

class PreVotePresenceCapture(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    election = models.ForeignKey(Election, on_delete=models.PROTECT)
    svt = models.ForeignKey(SVTToken, on_delete=models.PROTECT, null=True)
    channel = models.CharField(max_length=16, default='web')
    image = models.ImageField(upload_to='pre_vote_presence/%Y/%m/', blank=True, null=True)
    captured_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'election', 'svt')
