from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Role

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROLE SERIALIZER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['uuid', 'name', 'description', 'is_active']

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# USER SERIALIZERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class UserListSerializer(serializers.ModelSerializer):
    """List / retrieve for super-admin user management."""
    role_name = serializers.SerializerMethodField()
    role_uuid = serializers.SerializerMethodField()
    institution_uuid = serializers.SerializerMethodField()
    institution_name = serializers.SerializerMethodField()
    faculty_uuid = serializers.SerializerMethodField()
    department_uuid = serializers.SerializerMethodField()
    faculty_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'index_number', 'student_id', 'phone_number',
            'first_name', 'last_name', 'role', 'role_uuid', 'role_name',
            'institution_uuid', 'institution_name',
            'faculty_uuid', 'faculty_name', 'department_uuid', 'department_name',
            'is_active', 'is_verified', 'is_staff', 'is_superuser',
            'created_at', 'updated_at',
        ]

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

    def get_role_uuid(self, obj):
        return str(obj.role.uuid) if obj.role_id else None

    def get_institution_uuid(self, obj):
        return str(obj.institution.uuid) if obj.institution_id else None

    def get_institution_name(self, obj):
        return obj.institution.name if obj.institution_id else None

    def get_faculty_uuid(self, obj):
        return str(obj.faculty.uuid) if obj.faculty_id else None

    def get_department_uuid(self, obj):
        return str(obj.department.uuid) if obj.department_id else None

    def get_faculty_name(self, obj):
        return obj.faculty.name if obj.faculty_id else None

    def get_department_name(self, obj):
        return obj.department.name if obj.department_id else None


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer with create/update support"""
    role = RoleSerializer(read_only=True)
    role_uuid = serializers.UUIDField(write_only=True, required=False)
    role_name = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    institution_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    faculty_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    department_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    institution_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'index_number', 'student_id', 'phone_number',
            'first_name', 'last_name', 'role', 'role_uuid', 'role_name',
            'institution', 'institution_uuid', 'institution_name',
            'is_active', 'is_verified', 'is_staff', 'is_superuser',
            'onboarding_completed', 'faculty', 'department',
            'faculty_uuid', 'department_uuid',
            'password', 'created_at', 'updated_at',
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at', 'onboarding_completed', 'institution']

    def get_institution_name(self, obj):
        return obj.institution.name if obj.institution_id else None

    def _resolve_academic(self, validated_data):
        from elections.models import Faculty, Department

        faculty_uuid = validated_data.pop('faculty_uuid', serializers.empty)
        department_uuid = validated_data.pop('department_uuid', serializers.empty)

        if faculty_uuid is not serializers.empty:
            validated_data['faculty'] = (
                Faculty.objects.filter(uuid=faculty_uuid).first() if faculty_uuid else None
            )
        if department_uuid is not serializers.empty:
            validated_data['department'] = (
                Department.objects.filter(uuid=department_uuid).first() if department_uuid else None
            )
        return validated_data

    def _attach_main_ec(self, user, role, institution):
        from accounts.org import get_or_create_main_ec_unit
        from accounts.models import ECMembership

        if role and role.name == 'admin' and institution:
            main_unit = get_or_create_main_ec_unit(institution)
            ECMembership.objects.get_or_create(
                user=user,
                ec_unit=main_unit,
                defaults={'is_active': True},
            )

    def create(self, validated_data):
        from system.models import InstitutionProfile

        role_uuid = validated_data.pop('role_uuid', None)
        role_name = validated_data.pop('role_name', None)
        password = validated_data.pop('password', None)
        institution_uuid = validated_data.pop('institution_uuid', None)
        validated_data = self._resolve_academic(validated_data)

        if not role_uuid and not role_name:
            role = Role.objects.get(name='student')
        elif role_uuid:
            role = Role.objects.get(uuid=role_uuid)
        else:
            role = Role.objects.get(name=role_name)

        institution = None
        if institution_uuid:
            institution = InstitutionProfile.objects.filter(uuid=institution_uuid).first()

        user = User.objects.create_user(**validated_data)
        user.role = role
        if institution:
            user.institution = institution
        user.save()

        if password:
            user.set_password(password)
            user.save()

        self._attach_main_ec(user, role, institution)
        return user

    def update(self, instance, validated_data):
        from system.models import InstitutionProfile

        role_uuid = validated_data.pop('role_uuid', None)
        role_name = validated_data.pop('role_name', None)
        password = validated_data.pop('password', None)
        institution_uuid = validated_data.pop('institution_uuid', serializers.empty)
        validated_data = self._resolve_academic(validated_data)

        if role_uuid:
            role = Role.objects.get(uuid=role_uuid)
            instance.role = role
        elif role_name:
            role = Role.objects.get(name=role_name)
            instance.role = role

        if institution_uuid is not serializers.empty:
            if institution_uuid is None:
                instance.institution = None
            else:
                instance.institution = InstitutionProfile.objects.filter(uuid=institution_uuid).first()

        if password:
            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        self._attach_main_ec(instance, instance.role, instance.institution)
        return instance

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTHENTICATION SERIALIZERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128, required=False, allow_blank=True)

class OTPVerifySerializer(serializers.Serializer):
    otp_session_id = serializers.UUIDField()
    # Allow 5–6 digit real OTPs and DEBUG master codes (11111 / 111111)
    code = serializers.CharField(min_length=4, max_length=8)
