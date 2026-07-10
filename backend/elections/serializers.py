from rest_framework import serializers
from .models import Election, Position, VoterEligibility
from candidates.models import Candidate
from accounts.models import User

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['uuid', 'full_name', 'department', 'photo', 'manifesto', 'status', 'ballot_number']
        read_only_fields = ['uuid', 'created_at', 'updated_at']

class PositionSerializer(serializers.ModelSerializer):
    candidates = CandidateSerializer(many=True, read_only=True)
    
    class Meta:
        model = Position
        fields = ['uuid', 'title', 'description', 'max_votes_allowed', 'display_order', 'is_active', 'is_votable', 'candidates']
        read_only_fields = ['uuid', 'created_at', 'updated_at']

class ElectionSerializer(serializers.ModelSerializer):
    positions = PositionSerializer(many=True, read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Election
        fields = ['uuid', 'title', 'description', 'election_type', 'status', 'start_date', 'end_date',
                  'allow_web_voting', 'allow_ussd_voting', 'allow_sms_notifications',
                  'created_by', 'positions', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'created_by', 'created_at', 'updated_at']

class ElectionCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ['uuid', 'title', 'description', 'election_type', 'status', 'start_date', 'end_date',
                  'allow_web_voting', 'allow_ussd_voting', 'allow_sms_notifications']
        read_only_fields = ['uuid']

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uuid', 'email', 'index_number', 'first_name', 'last_name', 'phone_number']

class VoterEligibilitySerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    verified_by = UserBasicSerializer(read_only=True)
    user_uuid = serializers.UUIDField(write_only=True, required=False)
    user_identifier = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = VoterEligibility
        fields = ['uuid', 'election', 'user', 'user_uuid', 'user_identifier', 'is_eligible', 'verified_by', 'verified_at', 'created_at']
        read_only_fields = ['uuid', 'election', 'verified_by', 'verified_at', 'created_at']

    def create(self, validated_data):
        user_uuid = validated_data.pop('user_uuid', None)
        user_identifier = validated_data.pop('user_identifier', None)
        election = validated_data.get('election')
        request = self.context.get('request')
        user = None

        if user_uuid:
            user = User.objects.filter(uuid=user_uuid).first()
        elif user_identifier:
            user = User.objects.filter(email=user_identifier).first() or User.objects.filter(index_number=user_identifier).first()

        if not user:
            raise serializers.ValidationError({'user': 'User not found'})

        if VoterEligibility.objects.filter(election=election, user=user).exists():
            raise serializers.ValidationError({'user': 'User already eligible for this election'})

        validated_data['user'] = user
        validated_data['verified_by'] = request.user
        validated_data['verified_at'] = timezone.now()
        return super().create(validated_data)
