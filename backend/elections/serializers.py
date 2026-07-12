from django.utils import timezone
from rest_framework import serializers
from voting.models import Vote
from .models import Election, Position, VoterEligibility, Faculty, Department, Level
from candidates.models import Candidate
from accounts.models import User
from elections.services.eligibility import resolve_or_create_voter


class FacultySerializer(serializers.ModelSerializer):
    department_count = serializers.SerializerMethodField()

    class Meta:
        model = Faculty
        fields = ['uuid', 'name', 'code', 'description', 'is_active', 'department_count', 'created_at']
        read_only_fields = ['uuid', 'created_at']

    def get_department_count(self, obj):
        return obj.departments.filter(is_active=True).count()


class FacultyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faculty
        fields = ['name', 'code', 'description', 'is_active']

    def validate_code(self, value):
        return value.strip().upper()


class DepartmentSerializer(serializers.ModelSerializer):
    faculty = FacultySerializer(read_only=True)
    faculty_uuid = serializers.UUIDField(write_only=True, required=False)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    faculty_code = serializers.CharField(source='faculty.code', read_only=True)

    class Meta:
        model = Department
        fields = [
            'uuid', 'name', 'code', 'description', 'is_active',
            'faculty', 'faculty_uuid', 'faculty_name', 'faculty_code', 'created_at',
        ]
        read_only_fields = ['uuid', 'created_at']


class DepartmentWriteSerializer(serializers.ModelSerializer):
    faculty_uuid = serializers.UUIDField()

    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'is_active', 'faculty_uuid']

    def validate_code(self, value):
        return value.strip().upper()

    def create(self, validated_data):
        faculty_uuid = validated_data.pop('faculty_uuid')
        faculty = Faculty.objects.filter(uuid=faculty_uuid).first()
        if not faculty:
            raise serializers.ValidationError({'faculty_uuid': 'Faculty not found'})
        validated_data['faculty'] = faculty
        return super().create(validated_data)

    def update(self, instance, validated_data):
        faculty_uuid = validated_data.pop('faculty_uuid', None)
        if faculty_uuid:
            faculty = Faculty.objects.filter(uuid=faculty_uuid).first()
            if not faculty:
                raise serializers.ValidationError({'faculty_uuid': 'Faculty not found'})
            validated_data['faculty'] = faculty
        return super().update(instance, validated_data)


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['uuid', 'name', 'display_order', 'created_at']
        read_only_fields = ['uuid', 'created_at']


class LevelWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['name', 'display_order']

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
    eligible_voter_count = serializers.SerializerMethodField()
    votes_cast = serializers.SerializerMethodField()
    unique_voters = serializers.SerializerMethodField()

    class Meta:
        model = Election
        fields = [
            'uuid', 'title', 'description', 'election_type', 'status', 'start_date', 'end_date',
            'allow_web_voting', 'allow_ussd_voting', 'allow_sms_notifications',
            'scope_type', 'scope_faculty', 'scope_department', 'scope_level',
            'created_by', 'positions', 'eligible_voter_count', 'votes_cast', 'unique_voters',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_by', 'created_at', 'updated_at']

    scope_faculty = FacultySerializer(read_only=True)
    scope_department = DepartmentSerializer(read_only=True)
    scope_level = LevelSerializer(read_only=True)

    def get_eligible_voter_count(self, obj):
        return obj.eligibilities.filter(is_eligible=True).count()

    def get_votes_cast(self, obj):
        return Vote.objects.filter(election=obj).count()

    def get_unique_voters(self, obj):
        return Vote.objects.filter(election=obj).values('user').distinct().count()

class ElectionCreateUpdateSerializer(serializers.ModelSerializer):
    scope_faculty_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    scope_department_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    scope_level_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Election
        fields = [
            'uuid', 'title', 'description', 'election_type', 'status', 'start_date', 'end_date',
            'allow_web_voting', 'allow_ussd_voting', 'allow_sms_notifications',
            'scope_type', 'scope_faculty_uuid', 'scope_department_uuid', 'scope_level_uuid',
        ]
        read_only_fields = ['uuid']

    def validate(self, attrs):
        scope_type = attrs.get('scope_type', getattr(self.instance, 'scope_type', 'school'))
        faculty_uuid = attrs.get('scope_faculty_uuid')
        department_uuid = attrs.get('scope_department_uuid')
        level_uuid = attrs.get('scope_level_uuid')

        if scope_type == 'faculty' and not (faculty_uuid or getattr(self.instance, 'scope_faculty_id', None)):
            raise serializers.ValidationError({'scope_faculty_uuid': 'Faculty is required for faculty-scoped elections.'})
        if scope_type == 'department' and not (department_uuid or getattr(self.instance, 'scope_department_id', None)):
            raise serializers.ValidationError({'scope_department_uuid': 'Department is required for department-scoped elections.'})
        if scope_type == 'level' and not (level_uuid or getattr(self.instance, 'scope_level_id', None)):
            raise serializers.ValidationError({'scope_level_uuid': 'Level is required for level-scoped elections.'})
        return attrs

    def _resolve_scope(self, validated_data):
        faculty_uuid = validated_data.pop('scope_faculty_uuid', None)
        department_uuid = validated_data.pop('scope_department_uuid', None)
        level_uuid = validated_data.pop('scope_level_uuid', None)
        scope_type = validated_data.get('scope_type', getattr(self.instance, 'scope_type', None))

        if scope_type == 'school':
            validated_data['scope_faculty'] = None
            validated_data['scope_department'] = None
            validated_data['scope_level'] = None
            return validated_data

        if faculty_uuid is not None:
            validated_data['scope_faculty'] = Faculty.objects.filter(uuid=faculty_uuid).first()
        if department_uuid is not None:
            validated_data['scope_department'] = Department.objects.filter(uuid=department_uuid).first()
        if level_uuid is not None:
            validated_data['scope_level'] = Level.objects.filter(uuid=level_uuid).first()
        return validated_data

    def create(self, validated_data):
        validated_data = self._resolve_scope(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._resolve_scope(validated_data)
        return super().update(instance, validated_data)

class UserBasicSerializer(serializers.ModelSerializer):
    faculty = FacultySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    level = LevelSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'index_number', 'first_name', 'last_name', 'phone_number',
            'faculty', 'department', 'level', 'programme', 'onboarding_completed',
        ]

class VoterEligibilitySerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    verified_by = UserBasicSerializer(read_only=True)
    user_uuid = serializers.UUIDField(write_only=True, required=False)
    user_identifier = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = VoterEligibility
        fields = ['uuid', 'election', 'user', 'user_uuid', 'user_identifier', 'is_eligible', 'verified_by', 'verified_at', 'created_at']
        read_only_fields = ['uuid', 'election', 'verified_by', 'verified_at', 'created_at']

    def validate(self, data):
        if not data.get('user_uuid') and not (data.get('user_identifier') or '').strip():
            raise serializers.ValidationError({
                'user_identifier': 'Enter a student index number.',
            })
        identifier = (data.get('user_identifier') or '').strip()
        if identifier and '@' in identifier:
            raise serializers.ValidationError({
                'user_identifier': 'Students are identified by index number only.',
            })
        return data

    def create(self, validated_data):
        user_uuid = validated_data.pop('user_uuid', None)
        user_identifier = validated_data.pop('user_identifier', None)
        election = validated_data.get('election')
        request = self.context.get('request')
        user = None
        error_message = None

        if user_uuid:
            user = User.objects.filter(uuid=user_uuid).first()
            if not user:
                error_message = 'Student not found.'
        elif user_identifier:
            user, error_message = resolve_or_create_voter(user_identifier)

        if error_message:
            raise serializers.ValidationError({'user_identifier': error_message})

        if not user:
            raise serializers.ValidationError({
                'user_identifier': 'Enter a student index number.',
            })

        if VoterEligibility.objects.filter(election=election, user=user).exists():
            label = user.index_number or user.uuid
            raise serializers.ValidationError({
                'user_identifier': f'{label} is already eligible for this election.',
            })

        validated_data['user'] = user
        validated_data['verified_by'] = request.user
        validated_data['verified_at'] = timezone.now()
        return super().create(validated_data)
