from rest_framework.permissions import BasePermission


def get_role_name(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if user.is_superuser:
        return 'super_admin'
    if getattr(user, 'role_id', None) and user.role:
        return user.role.name
    if user.is_staff:
        return 'admin'
    if user.index_number:
        return 'student'
    return None


class IsAdmin(BasePermission):
    """Only Admin (EC) - full election management"""

    def has_permission(self, request, view):
        return get_role_name(request.user) == 'admin'


class IsSuperAdmin(BasePermission):
    """Only Super Admin - platform governance"""

    def has_permission(self, request, view):
        role = get_role_name(request.user)
        return role == 'super_admin' or bool(getattr(request.user, 'is_superuser', False))


class IsAdminOrSuperAdmin(BasePermission):
    """Both Admin and Super Admin can access"""

    def has_permission(self, request, view):
        role = get_role_name(request.user)
        return role in ['admin', 'super_admin'] or bool(getattr(request.user, 'is_superuser', False))


class IsAuditor(BasePermission):
    """Auditors, Admins, and Super Admins can access (view-only)"""

    def has_permission(self, request, view):
        role = get_role_name(request.user)
        return role in ['auditor', 'admin', 'super_admin'] or bool(getattr(request.user, 'is_superuser', False))


class IsStudentOrCandidate(BasePermission):
    """Students and Candidates can access"""

    def has_permission(self, request, view):
        role = get_role_name(request.user)
        return role in ['student', 'candidate']


class IsElectionViewer(BasePermission):
    """Election Committee, Auditors, and Super Admin can view election data."""

    def has_permission(self, request, view):
        role = get_role_name(request.user)
        return role in ['admin', 'auditor', 'super_admin'] or bool(getattr(request.user, 'is_superuser', False))


class IsElectionMonitorViewer(BasePermission):
    """Live election monitor — admin, auditor, and super admin."""

    def has_permission(self, request, view):
        role = get_role_name(request.user)
        return role in ['admin', 'auditor', 'super_admin'] or bool(getattr(request.user, 'is_superuser', False))


class IsStrongroomViewer(BasePermission):
    """Admin, Super Admin, and Auditor can access strongroom oversight."""

    def has_permission(self, request, view):
        role = get_role_name(request.user)
        return role in ['admin', 'super_admin', 'auditor']
