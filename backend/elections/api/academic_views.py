from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.governance import GovernanceBlocked, resolve_user_institution
from accounts.permissions import IsMainEC, IsSuperAdmin
from elections.models import Faculty, Department, InstitutionCategory
from elections.serializers import (
    FacultySerializer,
    DepartmentSerializer,
    InstitutionCategorySerializer,
)


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


class InstitutionCategoryListCreateView(APIView):
    """Main EC institution-wide categories used when building Main EC registers."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsMainEC()]

    def get(self, request):
        institution = resolve_user_institution(request.user)
        if not institution:
            return Response([])
        qs = InstitutionCategory.objects.filter(institution=institution).order_by('name')
        if not _wants_inactive(request):
            qs = qs.filter(is_active=True)
        return Response(InstitutionCategorySerializer(qs, many=True).data)

    def post(self, request):
        institution = resolve_user_institution(request.user)
        if not institution:
            return Response(
                {'detail': 'Your account is not linked to an institution.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = InstitutionCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data['name'].strip()
        if InstitutionCategory.objects.filter(institution=institution, name__iexact=name).exists():
            return Response(
                {'name': ['A category with this name already exists for your institution.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        category = serializer.save(institution=institution)
        return Response(InstitutionCategorySerializer(category).data, status=status.HTTP_201_CREATED)


class InstitutionCategoryDetailView(APIView):
    permission_classes = [IsMainEC]

    def _get(self, request, uuid):
        institution = resolve_user_institution(request.user)
        if not institution:
            raise GovernanceBlocked('No institution linked.', code='no_institution')
        return get_object_or_404(InstitutionCategory, uuid=uuid, institution=institution)

    def patch(self, request, uuid):
        try:
            category = self._get(request, uuid)
        except GovernanceBlocked as exc:
            return Response({'detail': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
        serializer = InstitutionCategorySerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data.get('name', category.name).strip()
        if (
            InstitutionCategory.objects.filter(institution=category.institution, name__iexact=name)
            .exclude(pk=category.pk)
            .exists()
        ):
            return Response(
                {'name': ['A category with this name already exists for your institution.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(InstitutionCategorySerializer(category).data)

    def delete(self, request, uuid):
        try:
            category = self._get(request, uuid)
        except GovernanceBlocked as exc:
            return Response({'detail': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
