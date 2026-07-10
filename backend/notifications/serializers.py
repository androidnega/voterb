from rest_framework import serializers
from .models import InAppNotification


class InAppNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InAppNotification
        fields = [
            'uuid', 'title', 'body', 'link', 'notification_type',
            'metadata', 'is_read', 'created_at',
        ]
        read_only_fields = fields
