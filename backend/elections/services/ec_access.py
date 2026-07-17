"""Main EC vs Sub EC election visibility and management rules.

Rules
-----
- Main EC creates / manages institutional (general) elections.
- Sub EC creates / manages category (faculty / department) elections.
- Main EC elections are invisible to Sub ECs.
- Sub EC elections are visible to Main EC, but Main EC cannot change them.
"""

from __future__ import annotations

from django.db.models import Q, QuerySet

from accounts.models import ECUnit, SubECAssignment
from accounts.org import (
    get_or_create_main_ec_unit,
    user_ec_memberships,
    user_is_main_ec,
    user_is_sub_ec,
)
from accounts.governance import resolve_user_institution
from elections.models import Election


class ElectionAccessBlocked(Exception):
    def __init__(self, message, code='election_access_blocked'):
        super().__init__(message)
        self.code = code


def user_sub_ec_units(user):
    return [
        m.ec_unit
        for m in user_ec_memberships(user).filter(ec_unit__unit_type=ECUnit.UNIT_SUB)
    ]


def user_main_ec_units(user):
    return [
        m.ec_unit
        for m in user_ec_memberships(user).filter(ec_unit__unit_type=ECUnit.UNIT_MAIN)
    ]


def resolve_create_owner(user) -> dict:
    """
    Resolve ownership fields for a new election based on the acting user.
    Raises ElectionAccessBlocked if the user cannot create elections.
    """
    institution = resolve_user_institution(user)
    if not institution:
        raise ElectionAccessBlocked(
            'Your account is not linked to an institution.',
            code='no_institution',
        )

    if user_is_main_ec(user) and not user_is_sub_ec(user):
        units = user_main_ec_units(user)
        unit = units[0] if units else get_or_create_main_ec_unit(institution)
        return {
            'owner_type': Election.OWNER_MAIN,
            'institution': institution,
            'owner_ec_unit': unit,
        }

    if user_is_sub_ec(user):
        units = user_sub_ec_units(user)
        if not units:
            raise ElectionAccessBlocked(
                'You are not assigned to a Sub EC unit.',
                code='no_sub_ec_unit',
            )
        unit = units[0]
        return {
            'owner_type': Election.OWNER_SUB,
            'institution': unit.institution or institution,
            'owner_ec_unit': unit,
        }

    if user_is_main_ec(user):
        # Prefer Main ownership when user somehow holds both
        units = user_main_ec_units(user)
        unit = units[0] if units else get_or_create_main_ec_unit(institution)
        return {
            'owner_type': Election.OWNER_MAIN,
            'institution': institution,
            'owner_ec_unit': unit,
        }

    raise ElectionAccessBlocked(
        'Only Main EC or Sub EC members can create elections.',
        code='forbidden',
    )


def elections_visible_to(user) -> QuerySet:
    """
    Elections the user may list / view.

    - Main EC / auditor (at institution): Main + Sub elections for their institution
    - Sub EC: only their own Sub EC unit's elections (never Main EC elections)
    - Super admin: all (platform oversight)
    """
    from accounts.permissions import get_role_name

    qs = Election.objects.all()
    role = get_role_name(user)

    if role == 'super_admin' or getattr(user, 'is_superuser', False):
        return qs

    institution = resolve_user_institution(user)

    if user_is_sub_ec(user) and not user_is_main_ec(user):
        unit_ids = [u.uuid for u in user_sub_ec_units(user)]
        if not unit_ids:
            return qs.none()
        return qs.filter(
            owner_type=Election.OWNER_SUB,
            owner_ec_unit_id__in=unit_ids,
        )

    if user_is_main_ec(user) or role == 'auditor':
        if not institution:
            # Legacy fallback: Main-owned or unscoped rows
            return qs.filter(Q(owner_type=Election.OWNER_MAIN) | Q(owner_type=''))
        return qs.filter(
            Q(institution=institution)
            | Q(institution__isnull=True, owner_type=Election.OWNER_MAIN)
        )

    return qs.none()


def user_can_manage_election(user, election: Election) -> bool:
    """True when the user may mutate this election (edit, open, close, positions, etc.)."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False

    # Main EC manages only Main-owned institutional elections
    if user_is_main_ec(user) and not user_is_sub_ec(user):
        if election.owner_type != Election.OWNER_MAIN:
            return False
        institution = resolve_user_institution(user)
        if election.institution_id and institution and election.institution_id != institution.uuid:
            return False
        return True

    # Sub EC manages only elections owned by their Sub EC unit
    if user_is_sub_ec(user):
        if election.owner_type != Election.OWNER_SUB:
            return False
        unit_ids = {u.uuid for u in user_sub_ec_units(user)}
        return bool(election.owner_ec_unit_id and election.owner_ec_unit_id in unit_ids)

    # Dual-hatted Main+Sub: manage Main elections as Main; Sub as Sub
    if user_is_main_ec(user):
        if election.owner_type == Election.OWNER_MAIN:
            institution = resolve_user_institution(user)
            if election.institution_id and institution and election.institution_id != institution.uuid:
                return False
            return True
        if election.owner_type == Election.OWNER_SUB:
            unit_ids = {u.uuid for u in user_sub_ec_units(user)}
            return bool(election.owner_ec_unit_id and election.owner_ec_unit_id in unit_ids)

    return False


def assert_can_manage_election(user, election: Election):
    if not user_can_manage_election(user, election):
        if user_is_main_ec(user) and election.owner_type == Election.OWNER_SUB:
            raise ElectionAccessBlocked(
                'This is a Sub EC election. Main EC can view it but cannot make changes.',
                code='sub_ec_readonly',
            )
        if user_is_sub_ec(user) and election.owner_type == Election.OWNER_MAIN:
            raise ElectionAccessBlocked(
                'Institutional elections are managed by Main EC only.',
                code='main_ec_only',
            )
        raise ElectionAccessBlocked(
            'You do not have permission to manage this election.',
            code='forbidden',
        )


def sub_ec_assignment_scope(ec_unit: ECUnit) -> dict:
    """Faculty / department UUIDs assigned to a Sub EC unit."""
    assignments = SubECAssignment.objects.filter(ec_unit=ec_unit)
    return {
        'faculty_uuids': {
            str(u) for u in assignments.exclude(faculty_id=None).values_list('faculty_id', flat=True)
        },
        'department_uuids': {
            str(u) for u in assignments.exclude(department_id=None).values_list('department_id', flat=True)
        },
    }


def register_matches_sub_ec_scope(register, ec_unit: ECUnit) -> bool:
    """
    True when the register has at least one category that intersects the
    Sub EC's faculty/department assignments.
    """
    if not register:
        return False
    scope = sub_ec_assignment_scope(ec_unit)
    if not scope['faculty_uuids'] and not scope['department_uuids']:
        return False
    cats = register.categories.select_related('faculty', 'department').all()
    for cat in cats:
        if cat.faculty_id and str(cat.faculty_id) in scope['faculty_uuids']:
            return True
        if cat.department_id and str(cat.department_id) in scope['department_uuids']:
            return True
    return False
