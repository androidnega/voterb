from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from accounts.permissions import IsSuperAdmin, IsAdminOrSuperAdmin, IsElectionViewer
from system.models import SystemSetting, FeatureFlag, InstitutionProfile, MaintenanceState
from system.serializers import (
    SystemSettingSerializer,
    FeatureFlagSerializer,
    InstitutionProfileSerializer,
    MaintenanceStateSerializer,
)


class CanReadFeatureFlags(BasePermission):
    """Super Admin, Main/Sub EC, and auditors can list feature flags."""

    def has_permission(self, request, view):
        return (
            IsSuperAdmin().has_permission(request, view)
            or IsElectionViewer().has_permission(request, view)
        )


class FeatureFlagListView(APIView):
    """Super Admin manages flags; Main/Sub EC and auditors may read them."""
    permission_classes = [CanReadFeatureFlags]

    def get(self, request):
        flags = FeatureFlag.objects.all().order_by('key')
        return Response(FeatureFlagSerializer(flags, many=True).data)


class FeatureFlagUpdateView(APIView):
    permission_classes = [IsSuperAdmin]

    def patch(self, request, key):
        flag = get_object_or_404(FeatureFlag, key=key)
        is_enabled = request.data.get('is_enabled')
        if is_enabled is None:
            return Response({'error': 'is_enabled is required'}, status=status.HTTP_400_BAD_REQUEST)
        flag.is_enabled = bool(is_enabled)
        flag.save(update_fields=['is_enabled', 'updated_at'])
        return Response(FeatureFlagSerializer(flag).data)


class InstitutionProfileView(APIView):
    permission_classes = [IsSuperAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile = InstitutionProfile.objects.first()
        if not profile:
            return Response({})
        return Response(InstitutionProfileSerializer(profile).data)

    def put(self, request):
        profile = InstitutionProfile.objects.first()
        if not profile:
            profile = InstitutionProfile(name=request.data.get('name', 'VoterB'))
        serializer = InstitutionProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        return self.put(request)


class MaintenanceStateView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        state = MaintenanceState.objects.order_by('-updated_at').first()
        if not state:
            state = MaintenanceState.objects.create(
                is_active=False,
                message='The system is currently under maintenance. Please check back later.',
            )
        return Response(MaintenanceStateSerializer(state).data)

    def put(self, request):
        state = MaintenanceState.objects.order_by('-updated_at').first()
        if not state:
            state = MaintenanceState()
        serializer = MaintenanceStateSerializer(state, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SystemSettingsByCategoryView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        category = request.query_params.get('category')
        queryset = SystemSetting.objects.all().order_by('key')
        if category:
            queryset = queryset.filter(category=category)
        return Response(SystemSettingSerializer(queryset, many=True).data)


class SystemSettingUpdateView(APIView):
    permission_classes = [IsSuperAdmin]

    def patch(self, request, key):
        setting, _ = SystemSetting.objects.get_or_create(key=key, defaults={'category': 'general'})
        value = request.data.get('value')
        if value is None:
            return Response({'error': 'value is required'}, status=status.HTTP_400_BAD_REQUEST)
        setting.value = str(value)
        if 'category' in request.data:
            setting.category = request.data['category']
        if 'description' in request.data:
            setting.description = request.data['description']
        setting.save()
        return Response(SystemSettingSerializer(setting).data)
