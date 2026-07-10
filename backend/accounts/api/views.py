from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from django.shortcuts import get_object_or_404

from accounts.models import User, MFALog, Role
from accounts.serializers import (
    LoginSerializer, OTPVerifySerializer, UserSerializer,
    AdminUserSerializer, UserWriteSerializer, RoleSerializer,
)
from accounts.services import OTPService, SessionService
from accounts.permissions import IsAdminOrSuperAdmin

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        identifier = serializer.validated_data['identifier']
        password = serializer.validated_data.get('password', '')

        # Try to find user by email or index_number
        user = User.objects.filter(email=identifier).first() or User.objects.filter(index_number=identifier).first()
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Determine if this is a staff login (has password)
        role_name = getattr(user.role, 'name', None)
        is_staff_user = user.is_staff or user.is_superuser or role_name in ['admin', 'super_admin', 'auditor']
        
        if is_staff_user:
            # Staff: require password
            if not password:
                return Response({'requires_password': True}, status=status.HTTP_200_OK)
            if not user.check_password(password):
                return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            # Student/Candidate: no password required
            pass

        # Generate OTP
        otp = OTPService.create_otp(user, purpose='login', channel='sms')
        MFALog.objects.create(user=user, event_type='login_otp_sent', ip_address=request.META.get('REMOTE_ADDR'))

        return Response({
            'requires_otp': True,
            'otp_session_id': str(otp.uuid),
            'is_staff': is_staff_user
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

        return Response({
            **tokens,
            'role': getattr(user.role, 'name', None),
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
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


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
