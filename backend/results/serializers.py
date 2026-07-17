from rest_framework import serializers

from accounts.models import User
from .models import ElectionResult


class ElectionBasicSerializer(serializers.ModelSerializer):
    class Meta:
        from elections.models import Election

        model = Election
        fields = ['uuid', 'title', 'description', 'status', 'start_date', 'end_date']


class CertifiedBySerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['uuid', 'email', 'first_name', 'last_name', 'display_name']

    def get_display_name(self, obj):
        parts = [obj.first_name, obj.last_name]
        name = ' '.join(p for p in parts if p).strip()
        if name:
            return name
        if obj.email:
            return obj.email
        return str(obj.uuid)


class ElectionResultSerializer(serializers.ModelSerializer):
    election = ElectionBasicSerializer(read_only=True)
    election_uuid = serializers.UUIDField(write_only=True, required=False)
    certified_by = CertifiedBySerializer(read_only=True)
    certified_by_email = serializers.SerializerMethodField()
    certified_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ElectionResult
        fields = [
            'uuid', 'election', 'election_uuid', 'status', 'standings', 'integrity_report',
            'result_hash', 'turnout_percentage', 'certified_by', 'certified_by_email',
            'certified_by_name', 'certified_at', 'certification_evidence', 'published_at',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'uuid', 'election', 'certified_by', 'certified_by_email', 'certified_by_name',
            'certified_at', 'certification_evidence', 'published_at', 'created_at', 'updated_at',
        ]

    def get_certified_by_email(self, obj):
        if obj.certified_by_id and getattr(obj.certified_by, 'email', None):
            return obj.certified_by.email
        evidence = obj.certification_evidence if isinstance(obj.certification_evidence, dict) else {}
        return evidence.get('certified_by') or None

    def get_certified_by_name(self, obj):
        if obj.certified_by_id:
            parts = [obj.certified_by.first_name, obj.certified_by.last_name]
            name = ' '.join(p for p in parts if p).strip()
            if name:
                return name
            if obj.certified_by.email:
                return obj.certified_by.email
        evidence = obj.certification_evidence if isinstance(obj.certification_evidence, dict) else {}
        return evidence.get('certified_by') or None

    def create(self, validated_data):
        validated_data.pop('election_uuid', None)
        return super().create(validated_data)
