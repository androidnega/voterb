from rest_framework import serializers
from candidates.models import Candidate
from elections.models import Position


class PositionSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['uuid', 'title']


class CandidateSerializer(serializers.ModelSerializer):
    position = PositionSimpleSerializer(read_only=True)
    position_uuid = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Candidate
        fields = [
            'uuid', 'election', 'position', 'position_uuid', 'full_name',
            'photo', 'manifesto', 'status', 'ballot_number',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'election', 'created_at', 'updated_at']

    def validate(self, attrs):
        if self.instance is None and not attrs.get('position_uuid'):
            raise serializers.ValidationError({'position_uuid': 'Position is required.'})
        return attrs

    def create(self, validated_data):
        position_uuid = validated_data.pop('position_uuid')
        validated_data['position'] = Position.objects.get(uuid=position_uuid)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'position_uuid' in validated_data:
            position_uuid = validated_data.pop('position_uuid')
            if position_uuid:
                validated_data['position'] = Position.objects.get(uuid=position_uuid)
        return super().update(instance, validated_data)
