"""Safe hard-delete for elections (clears PROTECT'd voting/security rows first)."""

from django.db import transaction

from security.models import SVTToken
from voting.models import PreVotePresenceCapture, Vote


def delete_election(election):
    """
    Remove an election and its vote/SVT/presence records.

    Votes and SVT tokens use on_delete=PROTECT so a plain Model.delete()
    fails once any ballots exist. Callers must already have checked
    authorization.
    """
    with transaction.atomic():
        Vote.objects.filter(election=election).delete()
        PreVotePresenceCapture.objects.filter(election=election).delete()
        SVTToken.objects.filter(election=election).delete()
        election.delete()
