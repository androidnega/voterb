from django.db.models import Count, Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, BasePermission
from accounts.permissions import IsMainEC, IsSuperAdmin
from elections.models import Faculty, Department
from elections.serializers import FacultySerializer, DepartmentSerializer


class IsMainECOrSuperAdmin(BasePermission):
    """Main EC owns institutional categories; Super Admin may seed platform defaults."""

    def has_permission(self, request, view):
        return IsMainEC().has_permission(request, view) or IsSuperAdmin().has_permission(request, view)


def _wants_inactive(request) -> bool:
    return request.query_params.get('include_inactive') in ('1', 'true', 'True')


class FacultyListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FacultySerializer

    def get_queryset(self):
        qs = Faculty.objects.annotate(
            active_department_count=Count(
                'departments',
                filter=Q(departments__is_active=True),
            )
        ).order_by('name')
        if not _wants_inactive(self.request):
            qs = qs.filter(is_active=True)
        return qs


class FacultyCreateView(generics.CreateAPIView):
    permission_classes = [IsMainECOrSuperAdmin]
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer


class DepartmentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DepartmentSerializer

    def get_queryset(self):
        qs = Department.objects.select_related('faculty').order_by('faculty__name', 'name')
        faculty_uuid = self.request.query_params.get('faculty')
        if faculty_uuid:
            qs = qs.filter(faculty__uuid=faculty_uuid)
        if not _wants_inactive(self.request):
            qs = qs.filter(is_active=True)
        return qs


class DepartmentCreateView(generics.CreateAPIView):
    permission_classes = [IsMainECOrSuperAdmin]
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
