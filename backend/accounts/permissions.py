from rest_framework.permissions import BasePermission

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROLE RESOLUTION HELPERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_role_name(user):
    """Resolve role name from user."""
    if not user or not user.is_authenticated:
        return None
    if user.is_superuser:
        return 'super_admin'
    if user.role and user.role.name:
        return user.role.name
    if user.is_staff:
        return 'admin'
    if user.index_number:
        return 'student'
    return None

def is_super_admin(user):
    return get_role_name(user) == 'super_admin'

def is_admin(user):
    """Main EC (legacy role name `admin`)."""
    return get_role_name(user) == 'admin'

def is_sub_ec(user):
    return get_role_name(user) == 'sub_ec'

def is_auditor(user):
    return get_role_name(user) == 'auditor'

def is_student(user):
    return get_role_name(user) in ['student', 'candidate']

def _main_ec(user):
    from accounts.org import user_is_main_ec
    return user_is_main_ec(user)

def _sub_ec(user):
    from accounts.org import user_is_sub_ec
    return user_is_sub_ec(user)

def is_election_manager(user):
    """Main EC only. Platform Super Admin has no election privileges."""
    return is_admin(user) or _main_ec(user)

def is_platform_manager(user):
    return is_super_admin(user)

def is_viewer(user):
    role = get_role_name(user)
    return role in ['admin', 'sub_ec', 'auditor']

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PERMISSION CLASSES (ALL APPS USE THESE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user) or _main_ec(request.user)

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return is_super_admin(request.user)

class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            is_admin(request.user)
            or is_super_admin(request.user)
            or _main_ec(request.user)
        )

class IsAuditor(BasePermission):
    def has_permission(self, request, view):
        # Super Admin is intentionally excluded from vote-cast audit trails.
        return is_auditor(request.user) or is_admin(request.user) or _main_ec(request.user) or _sub_ec(request.user)

class IsAuditorViewOnly(BasePermission):
    def has_permission(self, request, view):
        return is_auditor(request.user) or is_admin(request.user) or _main_ec(request.user) or _sub_ec(request.user)

    def has_object_permission(self, request, view, obj):
        if is_auditor(request.user):
            return request.method in ['GET', 'HEAD', 'OPTIONS']
        return True

# ─── ELECTION PERMISSIONS ───
class IsElectionViewer(BasePermission):
    def has_permission(self, request, view):
        role = get_role_name(request.user)
        return role in ['admin', 'sub_ec', 'auditor'] or _main_ec(request.user) or _sub_ec(request.user)

class IsElectionMonitorViewer(BasePermission):
    def has_permission(self, request, view):
        role = get_role_name(request.user)
        return (
            role in ['admin', 'sub_ec', 'auditor']
            or _main_ec(request.user)
            or _sub_ec(request.user)
        )

class IsElectionManager(BasePermission):
    def has_permission(self, request, view):
        return is_admin(request.user) or _main_ec(request.user)

class IsMainEC(BasePermission):
    """Institutional Main EC only (not Sub EC)."""
    def has_permission(self, request, view):
        return is_admin(request.user) or _main_ec(request.user)

class IsSubEC(BasePermission):
    def has_permission(self, request, view):
        return is_sub_ec(request.user) or _sub_ec(request.user)

class IsMainECOrSubEC(BasePermission):
    """Main EC or Sub EC — use with object-level election manage checks."""
    def has_permission(self, request, view):
        return IsMainEC().has_permission(request, view) or IsSubEC().has_permission(request, view)

# ─── STRONGROOM PERMISSIONS ───
class IsStrongroomViewer(BasePermission):
    """Main EC, Sub EC, and auditors — never Super Admin."""
    def has_permission(self, request, view):
        if is_super_admin(request.user):
            return False
        role = get_role_name(request.user)
        return (
            role in ['admin', 'sub_ec', 'auditor']
            or _main_ec(request.user)
            or _sub_ec(request.user)
        )

class IsStrongroomAdmin(BasePermission):
    """EC managers who can nominate/approve custody committees."""
    def has_permission(self, request, view):
        if is_super_admin(request.user):
            return False
        return is_admin(request.user) or _main_ec(request.user) or is_sub_ec(request.user) or _sub_ec(request.user)

# ─── STUDENT PERMISSIONS ───
class IsStudentOrCandidate(BasePermission):
    def has_permission(self, request, view):
        return is_student(request.user)

class IsAuthenticatedReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return is_admin(request.user) or _main_ec(request.user)
