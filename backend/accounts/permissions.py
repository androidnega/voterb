from rest_framework.permissions import BasePermission

class IsAdminOrSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_staff or request.user.is_superuser
        )


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        role = getattr(getattr(request.user, 'role', None), 'name', None)
        return role == 'super_admin'
