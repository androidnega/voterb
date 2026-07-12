from rest_framework import serializers
from .models import (
    BallotSeal, ElectionSeal, CustodyRecord, IntegrityVerification,
    StrongroomCommittee, StrongroomCommitteeMember,
    VaultAccessRequest, VaultSession, VaultEvidence
)
from accounts.models import User
from elections.models import Election

class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['uuid', 'email', 'first_name', 'last_name']

class ElectionBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Election
        fields = ['uuid', 'title', 'status']

class BallotSealSerializer(serializers.ModelSerializer):
    class Meta:
        model = BallotSeal
        fields = ['uuid', 'seal_hash', 'status', 'created_at']

class ElectionSealSerializer(serializers.ModelSerializer):
    class Meta:
        model = ElectionSeal
        fields = ['uuid', 'seal_hash', 'status', 'created_at']

class CustodyRecordSerializer(serializers.ModelSerializer):
    actor_email = serializers.SerializerMethodField()

    class Meta:
        model = CustodyRecord
        fields = ['uuid', 'action', 'metadata', 'timestamp', 'actor_email']

    def get_actor_email(self, obj):
        if obj.actor:
            return obj.actor.email or obj.actor.index_number
        return 'System'

# ---------- Committee ----------
class CommitteeMemberSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    user_uuid = serializers.UUIDField(write_only=True)

    class Meta:
        model = StrongroomCommitteeMember
        fields = ['uuid', 'user', 'user_uuid', 'role', 'joined_at']
        read_only_fields = ['uuid', 'joined_at']

    def create(self, validated_data):
        user_uuid = validated_data.pop('user_uuid')
        user = User.objects.get(uuid=user_uuid)
        validated_data['user'] = user
        return super().create(validated_data)

class StrongroomCommitteeSerializer(serializers.ModelSerializer):
    members = CommitteeMemberSerializer(many=True, read_only=True)
    nominated_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = StrongroomCommittee
        fields = ['uuid', 'election', 'status', 'nominated_by', 'members', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'created_at', 'updated_at']

# ---------- Vault Access ----------
class VaultAccessRequestSerializer(serializers.ModelSerializer):
    requested_by = UserBasicSerializer(read_only=True)
    reviewed_by = UserBasicSerializer(read_only=True)
    election = ElectionBasicSerializer(read_only=True)

    class Meta:
        model = VaultAccessRequest
        fields = ['uuid', 'election', 'requested_by', 'reason', 'status', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'created_at', 'updated_at']

class VaultSessionSerializer(serializers.ModelSerializer):
    access_request = VaultAccessRequestSerializer(read_only=True)
    opened_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = VaultSession
        fields = ['uuid', 'access_request', 'status', 'opened_by', 'opened_at', 'closed_at', 'evidence_notes']
        read_only_fields = ['uuid', 'opened_by', 'opened_at']

class VaultEvidenceSerializer(serializers.ModelSerializer):
    viewed_by = UserBasicSerializer(read_only=True)

    class Meta:
        model = VaultEvidence
        fields = ['uuid', 'seal_type', 'seal_hash', 'seal_uuid', 'viewed_by', 'viewed_at']
        read_only_fields = ['uuid', 'viewed_by', 'viewed_at']

# ---------- Combined Strongroom Detail ----------
class StrongroomElectionDetailSerializer(serializers.ModelSerializer):
    election_seal = ElectionSealSerializer(read_only=True)
    ballot_seals = BallotSealSerializer(many=True, read_only=True, source='ballot_seals')
    custody_records = serializers.SerializerMethodField()
    committee = StrongroomCommitteeSerializer(read_only=True)
    vault_requests = VaultAccessRequestSerializer(many=True, read_only=True)
    vault_sessions = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = ['uuid', 'title', 'status', 'election_seal', 'ballot_seals', 'custody_records',
                  'committee', 'vault_requests', 'vault_sessions']

    def get_custody_records(self, obj):
        records = CustodyRecord.objects.filter(election=obj).order_by('-timestamp')[:20]
        return CustodyRecordSerializer(records, many=True).data

    def get_vault_sessions(self, obj):
        sessions = VaultSession.objects.filter(access_request__election=obj).order_by('-opened_at')[:5]
        return VaultSessionSerializer(sessions, many=True).data
