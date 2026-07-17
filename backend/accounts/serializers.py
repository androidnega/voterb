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
    """List view serializer (read-only, role as string)"""
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['uuid', 'email', 'index_number', 'student_id', 'phone_number',
                  'first_name', 'last_name', 'role', 'role_name',
                  'is_active', 'is_verified', 'is_staff', 'is_superuser',
                  'created_at', 'updated_at']

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

class UserSerializer(serializers.ModelSerializer):
    """Full user serializer with create/update support"""
    role = RoleSerializer(read_only=True)
    role_uuid = serializers.UUIDField(write_only=True, required=False)
    role_name = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    institution_uuid = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['uuid', 'email', 'index_number', 'student_id', 'phone_number',
                  'first_name', 'last_name', 'role', 'role_uuid', 'role_name',
                  'institution', 'institution_uuid',
                  'is_active', 'is_verified', 'is_staff', 'is_superuser',
                  'onboarding_completed', 'faculty', 'department',
                  'password', 'created_at', 'updated_at']
        read_only_fields = ['uuid', 'created_at', 'updated_at', 'onboarding_completed', 'institution']

    def create(self, validated_data):
        from system.models import InstitutionProfile
        from accounts.org import get_or_create_main_ec_unit
        from accounts.models import ECMembership, ECUnit

        role_uuid = validated_data.pop('role_uuid', None)
        role_name = validated_data.pop('role_name', None)
        password = validated_data.pop('password', None)
        institution_uuid = validated_data.pop('institution_uuid', None)

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

        # Auto-attach Main EC membership when creating an admin under an institution
        if role.name == 'admin' and institution:
            main_unit = get_or_create_main_ec_unit(institution)
            ECMembership.objects.get_or_create(
                user=user,
                ec_unit=main_unit,
                defaults={'is_active': True},
            )

        return user

    def update(self, instance, validated_data):
        from system.models import InstitutionProfile

        role_uuid = validated_data.pop('role_uuid', None)
        role_name = validated_data.pop('role_name', None)
        password = validated_data.pop('password', None)
        institution_uuid = validated_data.pop('institution_uuid', serializers.empty)

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
