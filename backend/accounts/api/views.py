from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
from django.db import models as django_models
from django.shortcuts import get_object_or_404

from accounts.models import User, Role, MFALog, OTPRequest
from accounts.serializers import LoginSerializer, OTPVerifySerializer, UserSerializer, UserListSerializer, RoleSerializer
from accounts.services import OTPService, SessionService
from accounts.permissions import IsSuperAdmin, IsElectionManager, IsAdminOrSuperAdmin, get_role_name

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUTHENTICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class LoginView(APIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['identifier']
        password = serializer.validated_data.get('password', '')

        # Find user
        user = User.objects.filter(email=identifier).first() or User.objects.filter(index_number=identifier).first()
        
        # Auto-create student if eligible
        if not user and '@' not in identifier:
            from elections.models import VoterEligibility
            if VoterEligibility.objects.filter(user__index_number=identifier, is_eligible=True).exists():
                role, _ = Role.objects.get_or_create(name='student')
                user = User.objects.create(
                    index_number=identifier,
                    role=role,
                    is_active=True,
                    is_verified=True,
                    is_staff=False
                )
                print(f"🆕 Auto-created student: {identifier}")

        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if staff login requires password
        is_staff_user = user.is_staff or user.is_superuser or (user.role and user.role.name in ['admin', 'super_admin', 'auditor'])
        
        if is_staff_user:
            if not password:
                return Response({'requires_password': True}, status=status.HTTP_200_OK)
            if not user.check_password(password):
                return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate OTP
        otp = OTPService.create_otp(user, purpose='login', channel='sms')
        MFALog.objects.create(user=user, event_type='login_otp_sent', ip_address=request.META.get('REMOTE_ADDR'))

        return Response({
            'requires_otp': True,
            'otp_session_id': str(otp.uuid),
            'is_staff': is_staff_user,
            'is_new_user': not user.first_name and not user.last_name and not user.email
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

        role_name = user.role.name if user.role else None
        return Response({
            **tokens,
            'role': role_name,
            'role_name': role_name,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'index_number': user.index_number,
            'onboarding_completed': user.onboarding_completed,
            'is_new_user': not user.onboarding_completed and (
                not user.first_name and not user.last_name
            ),
        })

class OTPResendView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        otp_session_id = request.data.get('otp_session_id')
        if not otp_session_id:
            return Response({'error': 'OTP session ID required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            otp = OTPRequest.objects.get(uuid=otp_session_id, is_verified=False)
        except OTPRequest.DoesNotExist:
            return Response({'error': 'Invalid OTP session'}, status=status.HTTP_404_NOT_FOUND)
        new_otp = OTPService.create_otp(otp.user, purpose='login', channel='sms')
        otp.delete()
        return Response({'message': 'OTP resent', 'otp_session_id': str(new_otp.uuid)})

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
        from accounts.org import serialize_membership, user_ec_memberships, user_is_main_ec, user_is_sub_ec
        from accounts.governance import institution_governance_status, resolve_user_institution

        serializer = UserSerializer(request.user)
        data = serializer.data
        data['role_name'] = request.user.role.name if request.user.role else None
        data['is_main_ec'] = user_is_main_ec(request.user)
        data['is_sub_ec'] = user_is_sub_ec(request.user)
        institution = resolve_user_institution(request.user)
        if institution:
            data['institution'] = {
                'uuid': str(institution.uuid),
                'name': institution.name,
                'short_name': institution.short_name,
                'code': institution.code,
            }
        elif request.user.institution_id:
            inst = request.user.institution
            data['institution'] = {
                'uuid': str(inst.uuid),
                'name': inst.name,
                'short_name': inst.short_name,
                'code': inst.code,
            }
        else:
            data['institution'] = None
        data['governance'] = institution_governance_status(institution)
        data['ec_memberships'] = [
            serialize_membership(m) for m in user_ec_memberships(request.user)
        ]
        return Response(data)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STUDENT ONBOARDING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class StudentOnboardingOptionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from elections.models import Faculty, Department
        from elections.serializers import FacultySerializer, DepartmentSerializer

        faculties = Faculty.objects.filter(is_active=True)
        departments = Department.objects.filter(is_active=True).select_related('faculty')

        return Response({
            'faculties': FacultySerializer(faculties, many=True).data,
            'departments': DepartmentSerializer(departments, many=True).data,
        })

class StudentOnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.role.name not in ['student', 'candidate']:
            return Response({'error': 'Only students can complete onboarding'}, status=status.HTTP_403_FORBIDDEN)

        if user.onboarding_completed:
            return Response({'error': 'Onboarding already completed'}, status=status.HTTP_400_BAD_REQUEST)

        from elections.models import Faculty, Department

        faculty_uuid = request.data.get('faculty_uuid')
        department_uuid = request.data.get('department_uuid')
        programme = request.data.get('programme', '')
        phone_number = request.data.get('phone_number', user.phone_number)
        first_name = request.data.get('first_name', user.first_name)
        last_name = request.data.get('last_name', user.last_name)

        if not faculty_uuid or not department_uuid:
            return Response(
                {'error': 'Faculty and Department are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            faculty = Faculty.objects.get(uuid=faculty_uuid)
            department = Department.objects.get(uuid=department_uuid)

            if department.faculty != faculty:
                return Response(
                    {'error': 'Department does not belong to selected faculty'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.faculty = faculty
            user.department = department
            user.programme = programme
            user.phone_number = phone_number
            user.first_name = first_name
            user.last_name = last_name
            user.onboarding_completed = True
            user.save()

            return Response({
                'message': 'Onboarding completed successfully',
                'user': {
                    'uuid': user.uuid,
                    'email': user.email,
                    'index_number': user.index_number,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'faculty': user.faculty.name if user.faculty else None,
                    'department': user.department.name if user.department else None,
                }
            })
        except Faculty.DoesNotExist:
            return Response({'error': 'Faculty not found'}, status=status.HTTP_404_NOT_FOUND)
        except Department.DoesNotExist:
            return Response({'error': 'Department not found'}, status=status.HTTP_404_NOT_FOUND)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# USER MANAGEMENT – SUPER ADMIN ONLY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class UserListView(generics.ListCreateAPIView):
    permission_classes = [IsSuperAdmin]
    queryset = User.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserSerializer
        return UserListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search')
        role = self.request.query_params.get('role')
        is_active = self.request.query_params.get('is_active')

        if search:
            queryset = queryset.filter(
                django_models.Q(email__icontains=search) |
                django_models.Q(first_name__icontains=search) |
                django_models.Q(last_name__icontains=search) |
                django_models.Q(index_number__icontains=search) |
                django_models.Q(phone_number__icontains=search)
            )
        if role:
            queryset = queryset.filter(role__name=role)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsSuperAdmin]
    queryset = User.objects.all()
    lookup_field = 'uuid'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserSerializer
        return UserListSerializer

class UserActivateView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request, uuid):
        user = get_object_or_404(User, uuid=uuid)
        user.is_active = True
        user.save()
        return Response({'message': 'User activated'})

class UserDeactivateView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request, uuid):
        user = get_object_or_404(User, uuid=uuid)
        user.is_active = False
        user.save()
        return Response({'message': 'User deactivated'})

class UserResetPasswordView(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request, uuid):
        user = get_object_or_404(User, uuid=uuid)
        new_password = request.data.get('password')
        if not new_password or len(new_password) < 6:
            return Response({'error': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password reset successfully'})

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ROLE MANAGEMENT – SUPER ADMIN ONLY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RoleListView(generics.ListAPIView):
    permission_classes = [IsSuperAdmin]
    serializer_class = RoleSerializer
    queryset = Role.objects.filter(is_active=True)
