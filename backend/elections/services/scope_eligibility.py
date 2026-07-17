"""Election eligibility — voter register is the source of truth."""

from elections.models import VoterEligibility
from elections.services.register_service import user_is_on_election_register


def student_can_access_election(user, election):
    """
    A student can vote when they appear on the election's voter register.
    Falls back to legacy VoterEligibility when no registers exist yet.
    """
    if not user.is_active:
        return False

    if election.register_id or election.registers.exists():
        return user_is_on_election_register(user, election)

    return VoterEligibility.objects.filter(
        user=user,
        election=election,
        is_eligible=True,
    ).exists()
