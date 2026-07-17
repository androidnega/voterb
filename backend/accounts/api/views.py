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
from accounts.services import OTPService, SessionService, is_staff_otp_user, resolve_otp_phone
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
        raw_identifier = (serializer.validated_data['identifier'] or '').strip()
        password = serializer.validated_data.get('password', '')

        # Staff: email. Students: index number (normalized).
        is_email = '@' in raw_identifier
        identifier = raw_identifier.lower() if is_email else raw_identifier

        user = None
        if is_email:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            from elections.services.eligibility import normalize_index_input, resolve_or_create_voter
            from elections.models import VoterRegister, VoterRegisterEntry
            from elections.services.register_service import parse_full_name

            index = normalize_index_input(identifier)
            entries = list(
                VoterRegisterEntry.objects.filter(
                    voter_id__iexact=index,
                    register__approval_status=VoterRegister.APPROVAL_APPROVED,
                    register__replace_of__isnull=True,
                )
                .select_related('user', 'category', 'category__faculty', 'category__department')
                .order_by('-created_at')
            )
            if not entries:
                return Response(
                    {
                        'error': (
                            'This index number is not on an approved voter register. '
                            'Contact your electoral commission if you believe this is a mistake.'
                        ),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            entry = next((e for e in entries if e.user_id), entries[0])
            user = entry.user
            if not user:
                user, err = resolve_or_create_voter(index)
                if err or not user:
                    role, _ = Role.objects.get_or_create(name='student')
                    first_name, last_name = parse_full_name(entry.full_name)
                    user = User.objects.create(
                        index_number=index,
                        email=None,
                        first_name=first_name or 'Student',
                        last_name=last_name or '',
                        phone_number=entry.phone_number or '',
                        role=role,
                        is_active=True,
                        is_verified=True,
                        is_staff=False,
                        onboarding_completed=True,
                    )
                else:
                    # Fresh resolve — sync profile from the live register row.
                    first_name, last_name = parse_full_name(entry.full_name)
                    updates = ['onboarding_completed']
                    user.onboarding_completed = True
                    if first_name and user.first_name != first_name:
                        user.first_name = first_name[:150]
                        updates.append('first_name')
                    if last_name is not None and user.last_name != last_name:
                        user.last_name = (last_name or '')[:150]
                        updates.append('last_name')
                    if entry.phone_number and user.phone_number != entry.phone_number:
                        user.phone_number = entry.phone_number
                        updates.append('phone_number')
                    if not user.role_id or getattr(user.role, 'name', None) != 'student':
                        role, _ = Role.objects.get_or_create(name='student')
                        user.role = role
                        updates.append('role')
                    user.save(update_fields=list(dict.fromkeys(updates)))

            # Link every matching entry to this user and keep profile in sync.
            first_name, last_name = parse_full_name(entry.full_name)
            profile_updates = []
            if not user.onboarding_completed:
                user.onboarding_completed = True
                profile_updates.append('onboarding_completed')
            if first_name and (not user.first_name or user.first_name in ('Student',)):
                user.first_name = first_name[:150]
                profile_updates.append('first_name')
            if last_name and not user.last_name:
                user.last_name = last_name[:150]
                profile_updates.append('last_name')
            if entry.phone_number and not user.phone_number:
                user.phone_number = entry.phone_number
                profile_updates.append('phone_number')
            # Prefer faculty/department from the register category when present.
            cat = entry.category
            if cat:
                if cat.department_id and user.department_id != cat.department_id:
                    user.department = cat.department
                    user.faculty = cat.department.faculty if cat.department_id else user.faculty
                    profile_updates.extend(['department', 'faculty'])
                elif cat.faculty_id and user.faculty_id != cat.faculty_id:
                    user.faculty = cat.faculty
                    profile_updates.append('faculty')
            if profile_updates:
                user.save(update_fields=list(dict.fromkeys(profile_updates)))

            VoterRegisterEntry.objects.filter(
                pk__in=[e.pk for e in entries],
                user__isnull=True,
            ).update(user=user)

        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if staff login requires password
        is_staff_user = user.is_staff or user.is_superuser or (
            user.role and user.role.name in ['admin', 'super_admin', 'auditor', 'sub_ec']
        )

        if is_staff_user:
            if not password:
                return Response({'requires_password': True}, status=status.HTTP_200_OK)
            if not user.check_password(password):
                return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)

        # Generate OTP (SMS when a phone number is available)
        # Admin / Super Admin OTPs go to the shared ops number; they may also use 111111.
        otp = OTPService.create_otp(user, purpose='login', channel='sms')
        MFALog.objects.create(user=user, event_type='login_otp_sent', ip_address=request.META.get('REMOTE_ADDR'))

        otp_phone = resolve_otp_phone(user)
        masked_phone = ''
        if otp_phone:
            digits = ''.join(ch for ch in str(otp_phone) if ch.isdigit())
            masked_phone = f'***{digits[-4:]}' if len(digits) >= 4 else '***'

        if is_staff_otp_user(user):
            message = (
                f'OTP sent to phone ending {masked_phone}. '
                'You can also enter the staff master code.'
                if masked_phone
                else 'OTP generated. Enter the SMS code or the staff master code.'
            )
        else:
            message = (
                f'OTP sent to your phone ending {masked_phone}.'
                if masked_phone
                else 'OTP generated. Enter the code to continue.'
            )

        return Response({
            'requires_otp': True,
            'otp_session_id': str(otp.uuid),
            'is_staff': is_staff_user,
            'is_new_user': False,
            'onboarding_completed': bool(user.onboarding_completed) if not is_staff_user else True,
            'phone_hint': masked_phone,
            'message': message,
        })

class OTPVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp_session_id = serializer.validated_data['otp_session_id']
        code = ''.join(ch for ch in str(serializer.validated_data['code'] or '') if ch.isdigit())

        user = OTPService.verify_otp(otp_session_id, code)
        if not user:
            return Response({'error': 'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

        tokens = SessionService.create_session(user, request)
        MFALog.objects.create(user=user, event_type='otp_verified', ip_address=request.META.get('REMOTE_ADDR'))

        role_name = user.role.name if user.role else None
        # Register-based students are fully onboarded at index login — never send them
        # through the legacy faculty/department onboarding form.
        onboarding_completed = bool(getattr(user, 'onboarding_completed', False))
        if role_name in ('student', 'candidate') and not onboarding_completed:
            from elections.models import VoterRegister, VoterRegisterEntry
            on_register = VoterRegisterEntry.objects.filter(
                user=user,
                register__approval_status=VoterRegister.APPROVAL_APPROVED,
                register__replace_of__isnull=True,
            ).exists()
            if on_register:
                user.onboarding_completed = True
                user.save(update_fields=['onboarding_completed'])
                onboarding_completed = True

        return Response({
            **tokens,
            'role': role_name,
            'role_name': role_name,
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'index_number': user.index_number,
            'onboarding_completed': onboarding_completed,
            'is_new_user': False,
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
    """
    Legacy endpoint kept for compatibility.

    Student access is now index → approved register → OTP → dashboard.
    Faculty/department/level forms are no longer used.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        role_name = getattr(user.role, 'name', None) if user.role_id else None
        if role_name not in ['student', 'candidate']:
            return Response({'error': 'Only students can complete onboarding'}, status=status.HTTP_403_FORBIDDEN)

        # Always mark complete — register login is the source of truth.
        from elections.services.register_service import parse_full_name

        full_name = (request.data.get('full_name') or '').strip()
        phone_number = (request.data.get('phone_number') or user.phone_number or '').strip()
        if full_name:
            first_name, last_name = parse_full_name(full_name)
            user.first_name = first_name[:150]
            user.last_name = (last_name or '')[:150]
        if phone_number:
            user.phone_number = phone_number
        user.onboarding_completed = True
        user.save()

        return Response({
            'message': 'Profile saved. You can access your eligible elections.',
            'user': {
                'uuid': str(user.uuid),
                'email': user.email,
                'index_number': user.index_number,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone_number': user.phone_number,
                'onboarding_completed': True,
                'faculty': user.faculty.name if user.faculty_id else None,
                'department': user.department.name if user.department_id else None,
            },
        })

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
