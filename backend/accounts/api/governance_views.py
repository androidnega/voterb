"""Main EC dual-approval governance APIs."""

from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import make_password
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.governance import (
    GovernanceBlocked,
    assert_institution_ready,
    approve_main_ec_decision,
    decision_submitted_response,
    governance_applies_to_user,
    institution_governance_status,
    reject_main_ec_decision,
    resolve_user_institution,
    serialize_decision,
    submit_main_ec_decision,
)
from accounts.models import ECUnit, MainECDecision, User
from accounts.org import user_is_main_ec


class GovernanceStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        institution = resolve_user_institution(request.user)
        status_payload = institution_governance_status(institution)
        status_payload['governance_applies'] = governance_applies_to_user(request.user)
        status_payload['is_main_ec'] = user_is_main_ec(request.user)
        if institution:
            status_payload['institution'] = {
                'uuid': str(institution.uuid),
                'name': institution.name,
                'short_name': institution.short_name,
            }
        pending = 0
        if institution and user_is_main_ec(request.user):
            pending = MainECDecision.objects.filter(
                institution=institution,
                status=MainECDecision.STATUS_PENDING,
            ).count()
        status_payload['pending_decisions'] = pending
        return Response(status_payload)


class MainECDecisionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not user_is_main_ec(request.user):
            return Response({'detail': 'Main EC access required.'}, status=status.HTTP_403_FORBIDDEN)

        institution = resolve_user_institution(request.user)
        if not institution:
            return Response({'detail': 'No institution linked.'}, status=status.HTTP_400_BAD_REQUEST)

        qs = MainECDecision.objects.select_related('proposed_by', 'institution').prefetch_related(
            'approvals__user',
        )
        qs = qs.filter(institution=institution)
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        else:
            qs = qs.filter(status=MainECDecision.STATUS_PENDING)

        return Response([serialize_decision(d) for d in qs[:50]])


class MainECDecisionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        decision = get_object_or_404(
            MainECDecision.objects.select_related('proposed_by', 'institution').prefetch_related(
                'approvals__user',
            ),
            uuid=uuid,
        )
        if not user_is_main_ec(request.user):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        institution = resolve_user_institution(request.user)
        if decision.institution_id != getattr(institution, 'uuid', None):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        data = serialize_decision(decision)
        data['user_has_approved'] = decision.approvals.filter(user=request.user).exists()
        return Response(data)


class MainECDecisionApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid):
        decision = get_object_or_404(MainECDecision, uuid=uuid)
        try:
            decision = approve_main_ec_decision(
                decision,
                request.user,
                note=(request.data.get('note') or '').strip(),
            )
        except GovernanceBlocked as exc:
            return Response({'detail': str(exc), 'code': exc.code}, status=status.HTTP_400_BAD_REQUEST)

        data = serialize_decision(decision)
        if decision.status == MainECDecision.STATUS_ENROLLED:
            message = 'Decision enrolled — both Main EC members approved.'
        else:
            message = 'Approval recorded. Awaiting co-signature from the other Main EC member.'
        data['message'] = message
        return Response(data)


class MainECDecisionRejectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, uuid):
        decision = get_object_or_404(MainECDecision, uuid=uuid)
        try:
            decision = reject_main_ec_decision(
                decision,
                request.user,
                reason=(request.data.get('reason') or '').strip(),
            )
        except GovernanceBlocked as exc:
            return Response({'detail': str(exc), 'code': exc.code}, status=status.HTTP_400_BAD_REQUEST)
        data = serialize_decision(decision)
        data['message'] = 'Decision rejected.'
        return Response(data)


class MainECStructureView(APIView):
    """Main EC-only structure view and dual-approved Sub EC proposal endpoint."""

    permission_classes = [IsAuthenticated]

    def _institution(self, request):
        if not user_is_main_ec(request.user):
            return None
        return resolve_user_institution(request.user)

    def get(self, request):
        institution = self._institution(request)
        if not institution:
            return Response(
                {'detail': 'Only an institutional Main EC can manage Sub ECs.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        units = (
            ECUnit.objects.filter(
                institution=institution,
                unit_type=ECUnit.UNIT_SUB,
            )
            .select_related('parent')
            .prefetch_related(
                'memberships__user',
                'assignments__faculty',
                'assignments__department',
            )
            .order_by('name')
        )

        pending_by_unit = {}
        pending_updates = MainECDecision.objects.filter(
            institution=institution,
            status=MainECDecision.STATUS_PENDING,
            decision_type=MainECDecision.TYPE_SUB_EC_UPDATE,
        ).order_by('-created_at')
        for decision in pending_updates:
            unit_uuid = str((decision.payload or {}).get('unit_uuid') or '')
            if unit_uuid and unit_uuid not in pending_by_unit:
                pending_by_unit[unit_uuid] = {
                    'decision_uuid': str(decision.uuid),
                    'title': decision.title,
                    'approvals_received': decision.approvals.count(),
                    'approvals_required': 2,
                    'created_at': decision.created_at.isoformat(),
                }

        return Response({
            'institution': {
                'uuid': str(institution.uuid),
                'name': institution.name,
                'short_name': institution.short_name,
            },
            'governance': institution_governance_status(institution),
            'sub_ec_units': [
                {
                    'uuid': str(unit.uuid),
                    'name': unit.name,
                    'is_active': unit.is_active,
                    'pending_approval': pending_by_unit.get(str(unit.uuid)),
                    'members': [
                        {
                            'uuid': str(m.user.uuid),
                            'name': f'{m.user.first_name or ""} {m.user.last_name or ""}'.strip(),
                            'email': m.user.email,
                            'first_name': m.user.first_name or '',
                            'last_name': m.user.last_name or '',
                            'phone_number': m.user.phone_number or '',
                        }
                        for m in unit.memberships.filter(is_active=True)
                    ],
                    'faculties': [
                        {'uuid': str(a.faculty.uuid), 'name': a.faculty.name}
                        for a in unit.assignments.all()
                        if a.faculty_id
                    ],
                    'departments': [
                        {'uuid': str(a.department.uuid), 'name': a.department.name}
                        for a in unit.assignments.all()
                        if a.department_id
                    ],
                }
                for unit in units
            ],
        })

    def post(self, request):
        institution = self._institution(request)
        if not institution:
            return Response(
                {'detail': 'Only an institutional Main EC can propose a Sub EC.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        try:
            assert_institution_ready(request.user)
        except GovernanceBlocked as exc:
            return Response(
                {'detail': str(exc), 'code': exc.code},
                status=status.HTTP_403_FORBIDDEN,
            )

        unit_name = (request.data.get('unit_name') or '').strip()
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''
        if not unit_name:
            return Response({'unit_name': ['Unit name is required.']}, status=status.HTTP_400_BAD_REQUEST)
        if not email:
            return Response({'email': ['Email is required.']}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 8:
            return Response(
                {'password': ['Password must be at least 8 characters.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if User.objects.filter(email__iexact=email).exists():
            return Response({'email': ['A user with this email already exists.']}, status=status.HTTP_400_BAD_REQUEST)
        if ECUnit.objects.filter(institution=institution, name__iexact=unit_name).exists():
            return Response({'unit_name': ['An EC unit with this name already exists.']}, status=status.HTTP_400_BAD_REQUEST)

        faculty_uuids = request.data.get('faculty_uuids') or []
        department_uuids = request.data.get('department_uuids') or []
        if not faculty_uuids and not department_uuids:
            return Response(
                {'detail': 'Select at least one faculty or department.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        decision = submit_main_ec_decision(
            user=request.user,
            decision_type=MainECDecision.TYPE_SUB_EC_CREATE,
            title=f'Create Sub EC: {unit_name}',
            summary=(
                'Create a faculty/department Sub EC account and scoped unit. '
                'The other Main EC must approve before enrollment.'
            ),
            payload={
                'sub_ec': {
                    'unit_name': unit_name,
                    'email': email,
                    'password_hash': make_password(password),
                    'first_name': (request.data.get('first_name') or '').strip(),
                    'last_name': (request.data.get('last_name') or '').strip(),
                    'phone_number': (request.data.get('phone_number') or '').strip(),
                    'title': request.data.get('title') or 'member',
                    'faculty_uuids': faculty_uuids,
                    'department_uuids': department_uuids,
                },
            },
        )
        return decision_submitted_response(decision)


class MainECStructureUpdateView(APIView):
    """Propose an edit to an enrolled Sub EC — requires dual Main EC approval."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, unit_uuid):
        if not user_is_main_ec(request.user):
            return Response(
                {'detail': 'Only an institutional Main EC can propose Sub EC changes.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        institution = resolve_user_institution(request.user)
        if not institution:
            return Response({'detail': 'No institution linked.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            assert_institution_ready(request.user)
        except GovernanceBlocked as exc:
            return Response(
                {'detail': str(exc), 'code': exc.code},
                status=status.HTTP_403_FORBIDDEN,
            )

        unit = get_object_or_404(
            ECUnit,
            uuid=unit_uuid,
            institution=institution,
            unit_type=ECUnit.UNIT_SUB,
        )

        unit_name = (request.data.get('unit_name') or unit.name).strip()
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password') or ''
        faculty_uuids = request.data.get('faculty_uuids')
        department_uuids = request.data.get('department_uuids')

        if not unit_name:
            return Response({'unit_name': ['Unit name is required.']}, status=status.HTTP_400_BAD_REQUEST)
        if (
            ECUnit.objects.filter(institution=institution, name__iexact=unit_name)
            .exclude(uuid=unit.uuid)
            .exists()
        ):
            return Response({'unit_name': ['An EC unit with this name already exists.']}, status=status.HTTP_400_BAD_REQUEST)

        membership = (
            unit.memberships.filter(is_active=True).select_related('user').order_by('created_at').first()
        )
        member = membership.user if membership else None
        if email and User.objects.filter(email__iexact=email).exclude(
            pk=member.pk if member else None,
        ).exists():
            return Response({'email': ['A user with this email already exists.']}, status=status.HTTP_400_BAD_REQUEST)
        if password and len(password) < 8:
            return Response(
                {'password': ['Password must be at least 8 characters.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if faculty_uuids is not None or department_uuids is not None:
            faculty_uuids = faculty_uuids or []
            department_uuids = department_uuids or []
            if not faculty_uuids and not department_uuids:
                return Response(
                    {'detail': 'Select at least one faculty or department.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        sub_ec_payload = {
            'unit_name': unit_name,
            'email': email or (member.email if member else ''),
            'first_name': (request.data.get('first_name') if 'first_name' in request.data else (member.first_name if member else '')) or '',
            'last_name': (request.data.get('last_name') if 'last_name' in request.data else (member.last_name if member else '')) or '',
            'phone_number': (
                request.data.get('phone_number')
                if 'phone_number' in request.data
                else (member.phone_number if member else '')
            ) or '',
        }
        if 'is_active' in request.data:
            sub_ec_payload['is_active'] = bool(request.data.get('is_active'))
        if password:
            sub_ec_payload['password_hash'] = make_password(password)
        if faculty_uuids is not None:
            sub_ec_payload['faculty_uuids'] = faculty_uuids
            sub_ec_payload['department_uuids'] = department_uuids

        decision = submit_main_ec_decision(
            user=request.user,
            decision_type=MainECDecision.TYPE_SUB_EC_UPDATE,
            title=f'Update Sub EC: {unit_name}',
            summary=(
                'Update Sub EC account, status, or faculty/department scope. '
                'The other Main EC must approve before changes are applied.'
            ),
            payload={
                'unit_uuid': str(unit.uuid),
                'sub_ec': sub_ec_payload,
            },
        )
        return decision_submitted_response(decision)
