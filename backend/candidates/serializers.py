from rest_framework import serializers
from candidates.models import Candidate
from elections.models import Position

class PositionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['uuid', 'title']

class CandidateSerializer(serializers.ModelSerializer):
    position = PositionSimpleSerializer(read_only=True)
    position_uuid = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Candidate
        fields = ['uuid', 'election', 'position', 'position_uuid', 'full_name', 'department', 
                  'photo', 'manifesto', 'status', 'ballot_number', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'election', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        position_uuid = validated_data.pop('position_uuid')
        position = Position.objects.get(uuid=position_uuid)
        validated_data['position'] = position
        return super().create(validated_data)
