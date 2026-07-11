from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404

from accounts.models import User, MFALog, Role
from accounts.permissions import IsAdminOrSuperAdmin
from accounts.serializers import (
    LoginSerializer,
    OTPVerifySerializer,
    UserSerializer,
    AdminUserSerializer,
    UserWriteSerializer,
    RoleSerializer,
    StudentOnboardingSerializer,
)
from accounts.services import OTPService, SessionService


def resolve_role_name(user):
    if user.is_superuser:
        return 'super_admin'
    role_name = getattr(user.role, 'name', None)
    if role_name:
        return role_name
    if user.is_staff:
        return 'admin'
    if user.index_number:
        return 'student'
    return role_name


def student_auth_flags(user):
    role_name = resolve_role_name(user)
    is_student = role_name == 'student'
    requires_onboarding = is_student and not user.onboarding_completed
    return is_student, requires_onboarding


class LoginView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['identifier']
        password = serializer.validated_data.get('password', '')

        if '@' not in identifier:
            from elections.services.eligibility import normalize_index_input
            identifier = normalize_index_input(identifier)

        user = User.objects.filter(email=identifier).first() or User.objects.filter(index_number=identifier).first()
        is_new_user = False

        if not user and '@' not in identifier:
            from elections.models import VoterEligibility
            if VoterEligibility.objects.filter(user__index_number=identifier, is_eligible=True).exists():
                role, _ = Role.objects.get_or_create(name='student')
                user = User.objects.create(
                    index_number=identifier,
                    role=role,
                    is_active=True,
                    is_verified=True,
                    is_staff=False,
                )
                is_new_user = True
            else:
                return Response({'error': 'Index number not eligible for any election'}, status=status.HTTP_404_NOT_FOUND)

        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        role_name = getattr(user.role, 'name', None)
        is_staff_user = user.is_staff or user.is_superuser or role_name in ['admin', 'super_admin', 'auditor']

        if is_staff_user:
            if not password:
                return Response({'requires_password': True}, status=status.HTTP_200_OK)
            if not user.check_password(password):
                return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)

        otp = OTPService.create_otp(user, purpose='login', channel='sms')
        MFALog.objects.create(user=user, event_type='login_otp_sent', ip_address=request.META.get('REMOTE_ADDR'))

        _, requires_onboarding = student_auth_flags(user)
        if not is_new_user and requires_onboarding:
            is_new_user = True

        return Response({
            'requires_otp': True,
            'otp_session_id': str(otp.uuid),
            'is_staff': is_staff_user,
            'is_new_user': is_new_user,
            'requires_onboarding': requires_onboarding,
        })


class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp_session_id = serializer.validated_data['otp_session_id']
        code = serializer.validated_data['code']

        user = OTPService.verify_otp(otp_session_id, code)
        if not user:
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

        tokens = SessionService.create_session(user, request)
        MFALog.objects.create(user=user, event_type='otp_verified', ip_address=request.META.get('REMOTE_ADDR'))

        role_name = resolve_role_name(user)
        _, requires_onboarding = student_auth_flags(user)
        return Response({
            **tokens,
            'role': role_name,
            'role_name': role_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'index_number': user.index_number,
            'is_new_user': requires_onboarding,
            'requires_onboarding': requires_onboarding,
            'onboarding_completed': user.onboarding_completed,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            jti = token['jti']
            SessionService.revoke_session(jti)
            token.blacklist()
        except Exception:
            pass
        return Response({'message': 'Logged out successfully'})


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.select_related(
            'role', 'faculty', 'department', 'level'
        ).get(pk=request.user.pk)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class StudentOnboardingOptionsView(APIView):
    """Academic picklists for the student onboarding wizard."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = User.objects.select_related('role').get(pk=request.user.pk)
        role_name = resolve_role_name(user)
        if role_name != 'student':
            return Response(
                {'error': 'Only students can access onboarding options'},
                status=status.HTTP_403_FORBIDDEN,
            )

        from elections.models import Faculty, Department, Level
        from elections.serializers import FacultySerializer, DepartmentSerializer, LevelSerializer

        faculties = Faculty.objects.filter(is_active=True).order_by('name')
        departments = Department.objects.filter(
            is_active=True,
            faculty__is_active=True,
        ).select_related('faculty').order_by('faculty__name', 'name')
        levels = Level.objects.all().order_by('display_order', 'name')

        return Response({
            'faculties': FacultySerializer(faculties, many=True).data,
            'departments': DepartmentSerializer(departments, many=True).data,
            'levels': LevelSerializer(levels, many=True).data,
        })


class StudentOnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = User.objects.select_related('role').get(pk=request.user.pk)
        role_name = resolve_role_name(user)
        if role_name != 'student':
            return Response({'error': 'Only students can complete onboarding'}, status=status.HTTP_403_FORBIDDEN)

        if user.onboarding_completed:
            return Response({'error': 'Onboarding already completed'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = StudentOnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from elections.models import Faculty, Department, Level

        try:
            faculty = Faculty.objects.get(uuid=data['faculty_uuid'], is_active=True)
            department = Department.objects.get(uuid=data['department_uuid'], is_active=True)
            level = Level.objects.get(uuid=data['level_uuid'])
        except Faculty.DoesNotExist:
            return Response({'error': 'Faculty not found'}, status=status.HTTP_404_NOT_FOUND)
        except Department.DoesNotExist:
            return Response({'error': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)
        except Level.DoesNotExist:
            return Response({'error': 'Level not found'}, status=status.HTTP_404_NOT_FOUND)

        if department.faculty_id != faculty.id:
            return Response({'error': 'Department does not belong to selected faculty'}, status=status.HTTP_400_BAD_REQUEST)

        user.faculty = faculty
        user.department = department
        user.level = level
        user.programme = data.get('programme', '') or user.programme
        if data.get('phone_number'):
            user.phone_number = data['phone_number']
        if data.get('first_name'):
            user.first_name = data['first_name']
        if data.get('last_name'):
            user.last_name = data['last_name']

        level_digits = ''.join(ch for ch in level.name if ch.isdigit())
        user.year_of_study = int(level_digits) if level_digits else None
        user.onboarding_completed = True
        user.save()

        user = User.objects.select_related('role', 'faculty', 'department', 'level').get(pk=user.pk)
        return Response({
            'message': 'Onboarding completed successfully',
            'user': UserSerializer(user).data,
        })


class UserListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserWriteSerializer
        return AdminUserSerializer

    def get_queryset(self):
        qs = User.objects.select_related('role').order_by('-created_at')
        search = self.request.query_params.get('search')
        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')

        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(index_number__icontains=search)
            )
        if role:
            qs = qs.filter(role__name=role)
        if is_active in ('true', 'false'):
            qs = qs.filter(is_active=(is_active == 'true'))
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(AdminUserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    lookup_field = 'uuid'
    queryset = User.objects.select_related('role')

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UserWriteSerializer
        return AdminUserSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = UserWriteSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(AdminUserSerializer(user).data)


class UserActivateView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request, uuid):
        user = get_object_or_404(User, uuid=uuid)
        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response(AdminUserSerializer(user).data)


class UserDeactivateView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request, uuid):
        user = get_object_or_404(User, uuid=uuid)
        user.is_active = False
        user.save(update_fields=['is_active'])
        return Response(AdminUserSerializer(user).data)


class UserResetPasswordView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def post(self, request, uuid):
        user = get_object_or_404(User, uuid=uuid)
        password = request.data.get('password')
        if not password:
            return Response({'error': 'password is required'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(password)
        user.save(update_fields=['password'])
        return Response({'message': 'Password updated'})


class RoleListView(generics.ListAPIView):
    permission_classes = [IsAdminOrSuperAdmin]
    serializer_class = RoleSerializer
    queryset = Role.objects.filter(is_active=True).order_by('name')
