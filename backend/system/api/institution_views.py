"""Institution CRUD + Main/Sub EC management APIs."""

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import ECMembership, ECUnit, User
from accounts.permissions import IsMainEC, IsSuperAdmin
from accounts.serializers import UserListSerializer
from accounts.org import (
    create_main_ec_user,
    get_or_create_main_ec_unit,
    serialize_membership,
    user_institutions,
)
from accounts.governance import institution_governance_status, main_ec_member_count, REQUIRED_MAIN_EC_COUNT
from system.models import InstitutionProfile
from system.serializers import InstitutionProfileSerializer


class InstitutionListCreateView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        qs = InstitutionProfile.objects.all().order_by('name')
        data = []
        for inst in qs:
            row = InstitutionProfileSerializer(inst, context={'request': request}).data
            row['main_ec_count'] = main_ec_member_count(inst)
            row['governance'] = institution_governance_status(inst)
            row['sub_ec_count'] = ECUnit.objects.filter(
                institution=inst, unit_type=ECUnit.UNIT_SUB, is_active=True,
            ).count()
            data.append(row)
        return Response(data)

    def post(self, request):
        serializer = InstitutionProfileSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        institution = serializer.save()
        if not institution.code:
            base = (institution.short_name or institution.name or 'INST').upper().replace(' ', '')[:12]
            institution.code = base
            institution.save(update_fields=['code', 'updated_at'])
        get_or_create_main_ec_unit(institution)
        payload = InstitutionProfileSerializer(institution, context={'request': request}).data
        payload['main_ec_count'] = 0
        payload['governance'] = institution_governance_status(institution)
        payload['sub_ec_count'] = 0
        return Response(payload, status=status.HTTP_201_CREATED)


class InstitutionDetailView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request, uuid):
        institution = get_object_or_404(InstitutionProfile, uuid=uuid)
        data = InstitutionProfileSerializer(institution, context={'request': request}).data
        main_unit = ECUnit.objects.filter(
            institution=institution, unit_type=ECUnit.UNIT_MAIN,
        ).first()
        data['main_ec_unit'] = None
        data['main_ec_members'] = []
        data['sub_ec_units'] = []
        if main_unit:
            data['main_ec_unit'] = {
                'uuid': str(main_unit.uuid),
                'name': main_unit.name,
                'unit_type': main_unit.unit_type,
            }
            memberships = ECMembership.objects.filter(
                ec_unit=main_unit, is_active=True,
            ).select_related('user', 'user__role')
            data['main_ec_members'] = [
                {
                    **UserListSerializer(m.user).data,
                    'membership_uuid': str(m.uuid),
                }
                for m in memberships
            ]
        sub_units = ECUnit.objects.filter(
            institution=institution, unit_type=ECUnit.UNIT_SUB,
        ).prefetch_related('memberships__user')
        data['sub_ec_units'] = [
            {
                'uuid': str(u.uuid),
                'name': u.name,
                'unit_type': u.unit_type,
                'parent_uuid': str(u.parent_id) if u.parent_id else None,
                'member_count': u.memberships.filter(is_active=True).count(),
                'is_active': u.is_active,
            }
            for u in sub_units
        ]
        data['governance'] = institution_governance_status(institution)
        data['required_main_ec_count'] = REQUIRED_MAIN_EC_COUNT
        return Response(data)

    def patch(self, request, uuid):
        institution = get_object_or_404(InstitutionProfile, uuid=uuid)
        serializer = InstitutionProfileSerializer(
            institution, data=request.data, partial=True, context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class InstitutionMainECCreateView(APIView):
    """Super Admin creates a Main EC user under an institution."""
    permission_classes = [IsSuperAdmin]

    def post(self, request, uuid):
        institution = get_object_or_404(InstitutionProfile, uuid=uuid)
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''
        if not email:
            return Response({'email': ['Email is required.']}, status=status.HTTP_400_BAD_REQUEST)
        if not password or len(password) < 8:
            return Response(
                {'password': ['Password must be at least 8 characters.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(email__iexact=email).exists():
            return Response({'email': ['A user with this email already exists.']}, status=status.HTTP_400_BAD_REQUEST)

        user, membership, main_unit = create_main_ec_user(
            institution=institution,
            email=email,
            password=password,
            first_name=(request.data.get('first_name') or '').strip(),
            last_name=(request.data.get('last_name') or '').strip(),
            phone_number=(request.data.get('phone_number') or '').strip(),
        )
        return Response(
            {
                'user': UserListSerializer(user).data,
                'membership': serialize_membership(membership),
                'ec_unit': {
                    'uuid': str(main_unit.uuid),
                    'name': main_unit.name,
                    'unit_type': main_unit.unit_type,
                },
                'governance': institution_governance_status(institution),
            },
            status=status.HTTP_201_CREATED,
        )


class MyInstitutionsView(APIView):
    """Current user's institution + EC membership context."""
    permission_classes = [IsMainEC]

    def get(self, request):
        # Allow Main EC; Super Admin uses InstitutionListCreateView
        from accounts.permissions import is_super_admin
        if is_super_admin(request.user):
            institutions = InstitutionProfile.objects.filter(is_active=True)
        else:
            institutions = user_institutions(request.user)
        return Response([
            InstitutionProfileSerializer(i, context={'request': request}).data
            for i in institutions
        ])
