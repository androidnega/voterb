"""Election eligibility helpers combining voter lists and academic scope."""

from elections.models import VoterEligibility


def student_can_access_election(user, election):
    """
    A student can vote when they are on the election voter list,
    have completed onboarding, and match the election's academic scope.
    """
    if not user.is_active:
        return False

    role_name = getattr(user.role, 'name', None) if user.role_id else None
    if role_name == 'student' and not user.onboarding_completed:
        return False

    if not VoterEligibility.objects.filter(
        user=user,
        election=election,
        is_eligible=True,
    ).exists():
        return False

    return election.user_matches_scope(user)
