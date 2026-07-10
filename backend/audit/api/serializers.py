from rest_framework import serializers

from accounts.models import MFALog
from security.models import AuditLog


class MFALogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = MFALog
        fields = [
            'uuid', 'user', 'user_email', 'event_type', 'ip_address',
            'user_agent', 'metadata', 'created_at',
        ]

    def get_user_email(self, obj):
        if not obj.user:
            return None
        return obj.user.email or obj.user.index_number


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'audit_id', 'user', 'user_email', 'election', 'event_type',
            'ip_address', 'user_agent', 'metadata', 'timestamp',
        ]

    def get_user_email(self, obj):
        if not obj.user:
            return None
        return obj.user.email or obj.user.index_number
