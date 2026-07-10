from rest_framework import serializers
from fraud.models import SecurityAlert, FraudCase
from accounts.models import User
from elections.models import Election

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uuid', 'email', 'first_name', 'last_name']

class ElectionBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ['uuid', 'title']

class SecurityAlertSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    election = ElectionBasicSerializer(read_only=True)
    
    class Meta:
        model = SecurityAlert
        fields = ['uuid', 'alert_type', 'severity', 'user', 'election', 'description',
                  'status', 'risk_score', 'metadata', 'detected_at', 'updated_at']
        read_only_fields = ['uuid', 'detected_at', 'updated_at']

class FraudCaseSerializer(serializers.ModelSerializer):
    alert = SecurityAlertSerializer(read_only=True)
    investigator = UserBasicSerializer(read_only=True)
    alert_uuid = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = FraudCase
        fields = ['uuid', 'alert', 'alert_uuid', 'status', 'severity', 'risk_score',
                  'investigator', 'notes', 'resolved_at', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'investigator', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        alert_uuid = validated_data.pop('alert_uuid')
        alert = SecurityAlert.objects.get(uuid=alert_uuid)
        validated_data['alert'] = alert
        validated_data['severity'] = alert.severity
        validated_data['risk_score'] = alert.risk_score
        return super().create(validated_data)
