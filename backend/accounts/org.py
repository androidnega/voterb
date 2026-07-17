"""Institution / EC hierarchy helpers."""

from accounts.models import ECMembership, ECUnit, Role, User
from system.models import InstitutionProfile


def _role_name(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if getattr(user, 'is_superuser', False):
        return 'super_admin'
    if user.role_id and user.role and user.role.name:
        return user.role.name
    return None


def get_or_create_main_ec_unit(institution, name=None):
    """Ensure the institution has a Main EC unit."""
    unit_name = name or f'{institution.short_name or institution.name} EC'
    existing_main = ECUnit.objects.filter(
        institution=institution,
        unit_type=ECUnit.UNIT_MAIN,
        is_active=True,
    ).first()
    if existing_main:
        return existing_main
    unit, _ = ECUnit.objects.get_or_create(
        institution=institution,
        name=unit_name,
        defaults={'unit_type': ECUnit.UNIT_MAIN, 'is_active': True},
    )
    if unit.unit_type != ECUnit.UNIT_MAIN:
        unit.unit_type = ECUnit.UNIT_MAIN
        unit.save(update_fields=['unit_type', 'updated_at'])
    return unit


def user_ec_memberships(user, active_only=True):
    qs = ECMembership.objects.filter(user=user).select_related(
        'ec_unit', 'ec_unit__institution', 'ec_unit__parent',
    )
    if active_only:
        qs = qs.filter(is_active=True, ec_unit__is_active=True)
    return qs


def user_is_main_ec(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if _role_name(user) == 'admin':
        return True
    return user_ec_memberships(user).filter(ec_unit__unit_type=ECUnit.UNIT_MAIN).exists()


def user_is_sub_ec(user) -> bool:
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if _role_name(user) == 'sub_ec':
        return True
    return user_ec_memberships(user).filter(ec_unit__unit_type=ECUnit.UNIT_SUB).exists()


def user_institutions(user):
    """Institutions the user belongs to via membership or User.institution."""
    if not user or not getattr(user, 'is_authenticated', False):
        return InstitutionProfile.objects.none()
    if _role_name(user) == 'super_admin' or getattr(user, 'is_superuser', False):
        return InstitutionProfile.objects.filter(is_active=True)
    ids = set(
        user_ec_memberships(user).values_list('ec_unit__institution_id', flat=True)
    )
    if user.institution_id:
        ids.add(user.institution_id)
    return InstitutionProfile.objects.filter(uuid__in=ids, is_active=True)


def serialize_membership(membership: ECMembership) -> dict:
    unit = membership.ec_unit
    institution = unit.institution
    return {
        'uuid': str(membership.uuid),
        'ec_unit': {
            'uuid': str(unit.uuid),
            'name': unit.name,
            'unit_type': unit.unit_type,
            'parent_uuid': str(unit.parent_id) if unit.parent_id else None,
        },
        'institution': {
            'uuid': str(institution.uuid),
            'name': institution.name,
            'short_name': institution.short_name,
            'code': institution.code,
        },
    }


def create_main_ec_user(
    *,
    institution,
    email,
    password,
    first_name='',
    last_name='',
    phone_number='',
):
    """Create an admin (Main EC) user and attach to the institution Main EC unit."""
    role, _ = Role.objects.get_or_create(
        name='admin',
        defaults={'description': 'Main Electoral Commission'},
    )
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name or '',
        last_name=last_name or '',
        phone_number=phone_number or None,
        institution=institution,
        is_staff=True,
        is_verified=True,
    )
    user.role = role
    user.save(update_fields=['role', 'updated_at'])

    main_unit = get_or_create_main_ec_unit(institution)
    membership, _ = ECMembership.objects.get_or_create(
        user=user,
        ec_unit=main_unit,
        defaults={'is_active': True},
    )
    return user, membership, main_unit
