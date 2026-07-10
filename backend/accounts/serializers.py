from rest_framework import serializers
from .models import User, Role

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

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'index_number', 'phone_number',
            'first_name', 'last_name', 'role', 'role_name',
            'is_verified', 'is_staff', 'is_superuser',
        ]

    def get_role_name(self, obj):
        if obj.role_id and obj.role:
            return obj.role.name
        if obj.is_superuser:
            return 'super_admin'
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
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        if role_uuid is not None:
            self._set_role(instance, role_uuid)
        instance.save()
        return instance
