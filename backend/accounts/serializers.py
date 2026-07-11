from rest_framework import serializers
from .models import User, Role
from elections.serializers import FacultySerializer, DepartmentSerializer, LevelSerializer

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['uuid', 'name', 'description', 'is_active']

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, required=False, allow_blank=True)

class OTPVerifySerializer(serializers.Serializer):
    otp_session_id = serializers.UUIDField()
    code = serializers.CharField(max_length=6)


class StudentOnboardingSerializer(serializers.Serializer):
    faculty_uuid = serializers.UUIDField()
    department_uuid = serializers.UUIDField()
    level_uuid = serializers.UUIDField()
    programme = serializers.CharField(required=False, allow_blank=True, max_length=100)
    phone_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=300)
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate(self, attrs):
        full_name = (attrs.get('full_name') or '').strip()
        if full_name:
            parts = full_name.split(None, 1)
            attrs['first_name'] = parts[0]
            attrs['last_name'] = parts[1] if len(parts) > 1 else ''
        elif not (attrs.get('first_name') or '').strip() and not (attrs.get('last_name') or '').strip():
            raise serializers.ValidationError({'full_name': 'Full name is required.'})
        return attrs

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_name = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    faculty = FacultySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    level = LevelSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'index_number', 'phone_number',
            'first_name', 'last_name', 'display_name', 'role', 'role_name',
            'faculty', 'department', 'level', 'programme', 'year_of_study',
            'onboarding_completed',
            'is_verified', 'is_staff', 'is_superuser',
        ]

    def get_display_name(self, obj):
        parts = [obj.first_name, obj.last_name]
        name = ' '.join(p for p in parts if p).strip()
        if name:
            return name
        if obj.index_number:
            return obj.index_number
        if obj.email:
            return obj.email.split('@')[0]
        return 'User'

    def get_role_name(self, obj):
        if obj.is_superuser:
            return 'super_admin'
        if obj.role_id and obj.role:
            return obj.role.name
        if obj.is_staff:
            return 'admin'
        if obj.index_number:
            return 'student'
        return None


class AdminUserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'index_number', 'phone_number',
            'first_name', 'last_name', 'role', 'role_name',
            'is_active', 'is_staff', 'is_verified', 'created_at',
        ]

    def get_role_name(self, obj):
        return UserSerializer.get_role_name(self, obj)


class UserWriteSerializer(serializers.ModelSerializer):
    role_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'index_number',
            'phone_number', 'role_uuid', 'password',
        ]

    def _resolve_role(self, role_uuid):
        if role_uuid is None:
            return None
        role = Role.objects.filter(uuid=role_uuid).first()
        if not role:
            raise serializers.ValidationError({'role_uuid': 'Invalid role'})
        return role

    def _apply_role_rules(self, attrs, role, instance=None):
        email = attrs.get('email', getattr(instance, 'email', None) if instance else None)
        index_number = attrs.get('index_number', getattr(instance, 'index_number', None) if instance else None)
        role_name = role.name if role else (
            instance.role.name if instance and instance.role_id else None
        )

        if role_name == 'student':
            if not (attrs.get('index_number') or index_number):
                raise serializers.ValidationError({
                    'index_number': 'Index number is required for student accounts.',
                })
            attrs['email'] = None
        elif role_name in ('admin', 'super_admin', 'auditor', 'candidate'):
            if not (attrs.get('email') or email) and not instance:
                raise serializers.ValidationError({
                    'email': 'Email is required for staff accounts.',
                })
        return attrs

    def validate(self, attrs):
        role = self._resolve_role(attrs.get('role_uuid'))
        return self._apply_role_rules(attrs, role, self.instance)

    def _set_role(self, user, role_uuid):
        if role_uuid is None:
            return
        role = Role.objects.filter(uuid=role_uuid).first()
        if not role:
            raise serializers.ValidationError({'role_uuid': 'Invalid role'})
        user.role = role
        user.is_staff = role.name in ('admin', 'super_admin', 'auditor')

    def create(self, validated_data):
        role_uuid = validated_data.pop('role_uuid', None)
        password = validated_data.pop('password', None)
        role = self._resolve_role(role_uuid)
        if role:
            validated_data = self._apply_role_rules(validated_data, role)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        self._set_role(user, role_uuid)
        user.save()
        return user

    def update(self, instance, validated_data):
        role_uuid = validated_data.pop('role_uuid', None)
        password = validated_data.pop('password', None)
        role = self._resolve_role(role_uuid) if role_uuid is not None else instance.role
        validated_data = self._apply_role_rules(validated_data, role, instance)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        if role_uuid is not None:
            self._set_role(instance, role_uuid)
        instance.save()
        return instance
