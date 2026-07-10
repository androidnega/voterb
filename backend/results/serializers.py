from rest_framework import serializers
from .models import ElectionResult
from elections.models import Election

class ElectionBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ['uuid', 'title', 'status', 'start_date', 'end_date']

class ElectionResultSerializer(serializers.ModelSerializer):
    election = ElectionBasicSerializer(read_only=True)
    election_uuid = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = ElectionResult
        fields = ['uuid', 'election', 'election_uuid', 'status', 'standings', 'integrity_report',
                  'result_hash', 'turnout_percentage', 'certified_by', 'certified_at',
                  'published_at', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'election', 'certified_by', 'certified_at',
                           'published_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data.pop('election_uuid', None)
        return super().create(validated_data)
