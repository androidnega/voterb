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
    peer_ec = UserBasicSerializer(read_only=True)
    peer_approved_by = UserBasicSerializer(read_only=True)
    nominee_key_active = serializers.SerializerMethodField()

    class Meta:
        model = StrongroomCommittee
        fields = [
            'uuid', 'election', 'status', 'nominated_by', 'members',
            'peer_ec', 'peer_approved_by', 'peer_approved_at',
            'nominee_full_name', 'nominee_phone', 'nominee_email',
            'nominee_key_expires_at', 'nominee_key_sent_at', 'nominee_key_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']

    def get_nominee_key_active(self, obj):
        from django.utils import timezone
        if not obj.nominee_key_hash or not obj.nominee_key_expires_at:
            return False
        return obj.nominee_key_expires_at > timezone.now()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Never expose the hashed key material.
        data.pop('nominee_key_hash', None)
        # Mask phone for display.
        phone = data.get('nominee_phone') or ''
        if len(phone) >= 4:
            data['nominee_phone_masked'] = f'***{phone[-4:]}'
        else:
            data['nominee_phone_masked'] = '****'
        return data

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

def latest_committee(election):
    return election.committees.order_by('-updated_at').first()


def election_has_approved_committee(election):
    return election.committees.filter(status='approved').exists()


def has_any_approved_committee():
    return StrongroomCommittee.objects.filter(status='approved').exists()


# ---------- Committee overview (no vault session) ----------
class CommitteeOverviewSerializer(serializers.ModelSerializer):
    committee = serializers.SerializerMethodField()
    committee_status = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = ['uuid', 'title', 'status', 'committee', 'committee_status']

    def get_committee(self, obj):
        committee = latest_committee(obj)
        if not committee:
            return None
        return StrongroomCommitteeSerializer(committee).data

    def get_committee_status(self, obj):
        committee = latest_committee(obj)
        if not committee:
            return 'none'
        return committee.status


# ---------- Combined Strongroom Detail ----------
class StrongroomElectionDetailSerializer(serializers.ModelSerializer):
    election_seal = ElectionSealSerializer(read_only=True)
    ballot_seals = BallotSealSerializer(many=True, read_only=True)
    custody_records = serializers.SerializerMethodField()
    committee = serializers.SerializerMethodField()
    committee_status = serializers.SerializerMethodField()
    vault_requests = VaultAccessRequestSerializer(many=True, read_only=True)
    vault_sessions = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = [
            'uuid', 'title', 'status', 'election_seal', 'ballot_seals', 'custody_records',
            'committee', 'committee_status', 'vault_requests', 'vault_sessions',
        ]

    def get_custody_records(self, obj):
        records = CustodyRecord.objects.filter(election=obj).order_by('-timestamp')[:20]
        return CustodyRecordSerializer(records, many=True).data

    def get_committee(self, obj):
        committee = latest_committee(obj)
        if not committee:
            return None
        return StrongroomCommitteeSerializer(committee).data

    def get_committee_status(self, obj):
        committee = latest_committee(obj)
        if not committee:
            return 'none'
        return committee.status

    def get_vault_sessions(self, obj):
        sessions = VaultSession.objects.filter(access_request__election=obj).order_by('-opened_at')[:5]
        return VaultSessionSerializer(sessions, many=True).data
