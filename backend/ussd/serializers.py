from rest_framework import serializers
from .models import USSDSession, USSDRequestLog

class USSDRequestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = USSDRequestLog
        fields = ['uuid', 'request_payload', 'response_text', 'outcome', 'timestamp']

class USSDSessionSerializer(serializers.ModelSerializer):
    logs = USSDRequestLogSerializer(many=True, read_only=True)
    user_email = serializers.SerializerMethodField()
    election_title = serializers.SerializerMethodField()

    class Meta:
        model = USSDSession
        fields = [
            'uuid', 'provider_session_id', 'msisdn', 'user', 'user_email', 'election',
            'election_title', 'current_step', 'state_data', 'status', 'created_at',
            'updated_at', 'logs',
        ]

    def get_user_email(self, obj):
        return obj.user.email if obj.user else None

    def get_election_title(self, obj):
        return obj.election.title if obj.election else None
