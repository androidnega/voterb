from rest_framework import generics, permissions, status
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsSuperAdmin, get_role_name
from elections.models import Faculty, Department, Level
from elections.serializers import (
    FacultySerializer,
    FacultyWriteSerializer,
    DepartmentSerializer,
    DepartmentWriteSerializer,
    LevelSerializer,
    LevelWriteSerializer,
)


def _is_super_admin(user):
    role = get_role_name(user)
    return role == 'super_admin' or bool(getattr(user, 'is_superuser', False))


class FacultyListCreateView(generics.ListCreateAPIView):
    lookup_field = 'uuid'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsSuperAdmin()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FacultyWriteSerializer
        return FacultySerializer

    def get_queryset(self):
        qs = Faculty.objects.all().order_by('name')
        if not _is_super_admin(self.request.user):
            qs = qs.filter(is_active=True)
        elif self.request.query_params.get('active_only') == 'true':
            qs = qs.filter(is_active=True)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        faculty = serializer.save()
        return Response(FacultySerializer(faculty).data, status=status.HTTP_201_CREATED)


class FacultyDetailView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'uuid'
    queryset = Faculty.objects.all()

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsSuperAdmin()]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return FacultyWriteSerializer
        return FacultySerializer

    def get_queryset(self):
        qs = Faculty.objects.all()
        if not _is_super_admin(self.request.user):
            qs = qs.filter(is_active=True)
        return qs

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = FacultyWriteSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        faculty = serializer.save()
        return Response(FacultySerializer(faculty).data)

    def perform_destroy(self, instance):
        if User.objects.filter(faculty=instance).exists() or instance.departments.filter(is_active=True).exists():
            instance.is_active = False
            instance.save(update_fields=['is_active'])
        else:
            instance.delete()


class DepartmentListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsSuperAdmin()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DepartmentWriteSerializer
        return DepartmentSerializer

    def get_queryset(self):
        qs = Department.objects.select_related('faculty').order_by('faculty__name', 'name')
        if not _is_super_admin(self.request.user):
            qs = qs.filter(is_active=True, faculty__is_active=True)
        elif self.request.query_params.get('active_only') == 'true':
            qs = qs.filter(is_active=True, faculty__is_active=True)

        faculty_uuid = self.request.query_params.get('faculty_uuid')
        if faculty_uuid:
            qs = qs.filter(faculty__uuid=faculty_uuid)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = serializer.save()
        department = Department.objects.select_related('faculty').get(pk=department.pk)
        return Response(DepartmentSerializer(department).data, status=status.HTTP_201_CREATED)


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'uuid'

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsSuperAdmin()]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return DepartmentWriteSerializer
        return DepartmentSerializer

    def get_queryset(self):
        qs = Department.objects.select_related('faculty')
        if not _is_super_admin(self.request.user):
            qs = qs.filter(is_active=True, faculty__is_active=True)
        return qs

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = DepartmentWriteSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        department = serializer.save()
        department = Department.objects.select_related('faculty').get(pk=department.pk)
        return Response(DepartmentSerializer(department).data)

    def perform_destroy(self, instance):
        if User.objects.filter(department=instance).exists():
            instance.is_active = False
            instance.save(update_fields=['is_active'])
        else:
            instance.delete()


class LevelListCreateView(generics.ListCreateAPIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsSuperAdmin()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return LevelWriteSerializer
        return LevelSerializer

    def get_queryset(self):
        return Level.objects.all().order_by('display_order', 'name')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        level = serializer.save()
        return Response(LevelSerializer(level).data, status=status.HTTP_201_CREATED)


class LevelDetailView(generics.RetrieveUpdateDestroyAPIView):
    lookup_field = 'uuid'
    queryset = Level.objects.all()

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return [IsSuperAdmin()]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return LevelWriteSerializer
        return LevelSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = LevelWriteSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        level = serializer.save()
        return Response(LevelSerializer(level).data)

    def perform_destroy(self, instance):
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if User.objects.filter(level=instance).exists():
            return Response(
                {'error': 'Cannot delete level assigned to students. Reassign students first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
