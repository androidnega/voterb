from rest_framework import serializers

from accounts.models import MFALog
from security.models import AuditLog, DeviceLog, LocationLog
from security.services.vote_audit import sanitize_audit_metadata


class DeviceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceLog
        fields = [
            'device_log_id',
            'browser_fingerprint',
            'device_type',
            'operating_system',
            'user_agent',
            'last_seen_at',
        ]


class LocationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationLog
        fields = [
            'location_log_id',
            'ip_address',
            'country',
            'region',
            'city',
            'latitude',
            'longitude',
            'last_seen_at',
        ]


class VoteAuditListSerializer(serializers.ModelSerializer):
    """List payload for voter audits — never includes ballot choices."""

    user_email = serializers.SerializerMethodField()
    user_display = serializers.SerializerMethodField()
    election_title = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    device_type = serializers.SerializerMethodField()
    operating_system = serializers.SerializerMethodField()
    has_presence_photo = serializers.SerializerMethodField()
    confirmation_code = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'audit_id',
            'type',
            'user',
            'user_email',
            'user_display',
            'election',
            'election_title',
            'event_type',
            'ip_address',
            'device_type',
            'operating_system',
            'has_presence_photo',
            'confirmation_code',
            'timestamp',
        ]

    def get_type(self, obj):
        return 'vote'

    def get_user_email(self, obj):
        if not obj.user:
            return None
        return obj.user.email or obj.user.index_number

    def get_user_display(self, obj):
        if not obj.user:
            return 'Unknown voter'
        name = f'{obj.user.first_name or ""} {obj.user.last_name or ""}'.strip()
        return name or obj.user.email or obj.user.index_number or str(obj.user.uuid)

    def get_election_title(self, obj):
        return obj.election.title if obj.election_id else None

    def get_device_type(self, obj):
        if obj.device_log_id:
            return obj.device_log.device_type
        return (obj.metadata or {}).get('device', {}).get('device_type')

    def get_operating_system(self, obj):
        if obj.device_log_id:
            return obj.device_log.operating_system
        return (obj.metadata or {}).get('device', {}).get('operating_system')

    def get_has_presence_photo(self, obj):
        return bool(obj.presence_capture_id)

    def get_confirmation_code(self, obj):
        meta = sanitize_audit_metadata(obj.metadata or {})
        return meta.get('confirmation_code')


class VoteAuditDetailSerializer(VoteAuditListSerializer):
    device = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    presence_photo_url = serializers.SerializerMethodField()
    presence_captured_at = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    user_agent = serializers.CharField()

    class Meta(VoteAuditListSerializer.Meta):
        fields = VoteAuditListSerializer.Meta.fields + [
            'user_agent',
            'device',
            'location',
            'presence_photo_url',
            'presence_captured_at',
            'metadata',
        ]

    def get_metadata(self, obj):
        return sanitize_audit_metadata(obj.metadata or {})

    def get_device(self, obj):
        if obj.device_log_id:
            data = DeviceLogSerializer(obj.device_log).data
            meta_device = sanitize_audit_metadata((obj.metadata or {}).get('device') or {})
            for key in (
                'browser_name',
                'browser_version',
                'platform',
                'platform_version',
                'architecture',
                'hints_source',
                'timezone',
                'languages',
                'screen',
                'hardware_concurrency',
                'device_memory_gb',
                'touch_points',
            ):
                if key in meta_device and meta_device[key] not in (None, '', []):
                    data[key] = meta_device[key]
            return data
        return sanitize_audit_metadata((obj.metadata or {}).get('device') or {})

    def get_location(self, obj):
        if obj.location_log_id:
            data = LocationLogSerializer(obj.location_log).data
            meta_loc = sanitize_audit_metadata((obj.metadata or {}).get('location') or {})
            if meta_loc.get('accuracy_m') is not None:
                data = {**data, 'accuracy_m': meta_loc.get('accuracy_m')}
            return data
        return sanitize_audit_metadata((obj.metadata or {}).get('location') or {})

    def _presence(self, obj):
        if not obj.presence_capture_id:
            return None
        from voting.models import PreVotePresenceCapture

        return (
            PreVotePresenceCapture.objects.filter(uuid=obj.presence_capture_id)
            .exclude(image='')
            .first()
        )

    def get_presence_photo_url(self, obj):
        capture = self._presence(obj)
        if not capture or not capture.image:
            return None
        request = self.context.get('request')
        url = capture.image.url
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_presence_captured_at(self, obj):
        capture = self._presence(obj)
        if not capture:
            return None
        return capture.captured_at.isoformat()


class MFALogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = MFALog
        fields = [
            'uuid', 'user', 'user_email', 'event_type', 'ip_address',
            'user_agent', 'metadata', 'created_at',
        ]

    def get_user_email(self, obj):
        if not obj.user:
            return None
        return obj.user.email or obj.user.index_number


class AuditLogSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'audit_id', 'user', 'user_email', 'election', 'event_type',
            'ip_address', 'user_agent', 'metadata', 'timestamp',
        ]

    def get_user_email(self, obj):
        if not obj.user:
            return None
        return obj.user.email or obj.user.index_number

    def get_metadata(self, obj):
        return sanitize_audit_metadata(obj.metadata or {})
