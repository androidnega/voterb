from rest_framework import serializers
from .models import SystemSetting, FeatureFlag, InstitutionProfile, MaintenanceState


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ['uuid', 'key', 'value', 'category', 'description', 'updated_at']
        read_only_fields = ['uuid', 'updated_at']


class FeatureFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureFlag
        fields = ['uuid', 'key', 'is_enabled', 'description', 'category', 'updated_at']
        read_only_fields = ['uuid', 'updated_at']


class InstitutionProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstitutionProfile
        fields = [
            'uuid', 'name', 'short_name', 'code', 'primary_color', 'secondary_color',
            'contact_email', 'contact_phone', 'address', 'logo',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class MaintenanceStateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceState
        fields = [
            'id', 'is_active', 'message', 'scheduled_start',
            'scheduled_end', 'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']
