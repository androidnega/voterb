"""Institutional voter registers — Main EC creates register and assigns categories."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.governance import assert_institution_ready, resolve_user_institution, GovernanceBlocked
from accounts.permissions import IsMainEC
from elections.models import (
    VoterCategory,
    VoterRegister,
    VoterRegisterEntry,
)
from elections.serializers import (
    VoterCategorySerializer,
    VoterRegisterEntrySerializer,
    VoterRegisterSerializer,
    VoterRegisterWriteSerializer,
)
from elections.services.register_service import import_register_csv


def _institution_for(request):
    institution = resolve_user_institution(request.user)
    if not institution:
        raise GovernanceBlocked(
            'Your account is not linked to an institution.',
            code='no_institution',
        )
    return institution


def _register_for_institution(request, register_uuid):
    institution = _institution_for(request)
    return get_object_or_404(
        VoterRegister.objects.prefetch_related('categories', 'entries'),
        uuid=register_uuid,
        institution=institution,
    )


class InstitutionRegisterListCreateView(APIView):
    """Main EC: list / create institutional voter registers."""
    permission_classes = [IsMainEC]

    def get(self, request):
        try:
            institution = _institution_for(request)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
        qs = (
            VoterRegister.objects.filter(institution=institution, replace_of__isnull=True)
            .prefetch_related('categories', 'entries', 'pending_replacements')
            .order_by('name')
        )
        return Response(VoterRegisterSerializer(qs, many=True).data)

    def post(self, request):
        try:
            institution = assert_institution_ready(request.user)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)

        serializer = VoterRegisterWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        name = serializer.validated_data['name'].strip()
        if VoterRegister.objects.filter(institution=institution, name__iexact=name).exists():
            return Response(
                {'name': ['A register with this name already exists for your institution.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        institution_category_uuids = request.data.get('institution_category_uuids') or []
        if request.data.get('institution_category_uuid'):
            institution_category_uuids = list(institution_category_uuids) + [
                request.data.get('institution_category_uuid')
            ]
        faculty_uuids = request.data.get('faculty_uuids') or []
        department_uuids = request.data.get('department_uuids') or []
        # Backward compatible singular fields
        if request.data.get('faculty_uuid'):
            faculty_uuids = list(faculty_uuids) + [request.data.get('faculty_uuid')]
        if request.data.get('department_uuid'):
            department_uuids = list(department_uuids) + [request.data.get('department_uuid')]

        # Deduplicate while preserving order
        seen_i, seen_f, seen_d = set(), set(), set()
        institution_category_uuids = [
            str(u) for u in institution_category_uuids
            if u and not (str(u) in seen_i or seen_i.add(str(u)))
        ]
        faculty_uuids = [
            str(u) for u in faculty_uuids
            if u and not (str(u) in seen_f or seen_f.add(str(u)))
        ]
        department_uuids = [
            str(u) for u in department_uuids
            if u and not (str(u) in seen_d or seen_d.add(str(u)))
        ]

        has_institution = bool(institution_category_uuids)
        has_sub = bool(faculty_uuids or department_uuids)
        if has_institution and has_sub:
            return Response(
                {
                    'error': (
                        'Choose either institution categories (Main EC) or '
                        'faculty/department categories (Sub EC), not both.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not has_institution and not has_sub:
            return Response(
                {
                    'error': (
                        'Select at least one category. Create an Institution category under '
                        'Categories for Main EC, or choose a faculty/department for Sub EC.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from elections.models import InstitutionCategory

        institution_categories = []
        if has_institution:
            institution_categories = list(
                InstitutionCategory.objects.filter(
                    institution=institution,
                    uuid__in=institution_category_uuids,
                    is_active=True,
                )
            )
            found = {str(c.uuid) for c in institution_categories}
            missing = [u for u in institution_category_uuids if u not in found]
            if missing:
                return Response(
                    {'institution_category_uuids': ['One or more institution categories were not found.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Preserve selection order
            by_id = {str(c.uuid): c for c in institution_categories}
            institution_categories = [by_id[u] for u in institution_category_uuids if u in by_id]

        audience = (
            VoterRegister.AUDIENCE_MAIN if has_institution else VoterRegister.AUDIENCE_SUB
        )

        from django.db import transaction
        from accounts.governance import serialize_decision, submit_main_ec_decision
        from accounts.models import MainECDecision

        categories = []
        with transaction.atomic():
            register = serializer.save(
                institution=institution,
                election=None,
                created_by=request.user,
                name=name,
                audience=audience,
                approval_status=VoterRegister.APPROVAL_PENDING,
            )
            if audience == VoterRegister.AUDIENCE_MAIN:
                for inst_cat in institution_categories:
                    cat_serializer = VoterCategorySerializer(data={
                        'name': inst_cat.name,
                        'description': inst_cat.description or '',
                    })
                    cat_serializer.is_valid(raise_exception=True)
                    categories.append(cat_serializer.save(register=register))
            else:
                for faculty_uuid in faculty_uuids:
                    cat_serializer = VoterCategorySerializer(data={'faculty_uuid': faculty_uuid})
                    cat_serializer.is_valid(raise_exception=True)
                    categories.append(cat_serializer.save(register=register))
                for department_uuid in department_uuids:
                    cat_serializer = VoterCategorySerializer(data={'department_uuid': department_uuid})
                    cat_serializer.is_valid(raise_exception=True)
                    categories.append(cat_serializer.save(register=register))

        primary = categories[0]
        category_names = ', '.join(c.name for c in categories[:4])
        if len(categories) > 4:
            category_names += f' (+{len(categories) - 4} more)'

        if audience == VoterRegister.AUDIENCE_MAIN:
            summary = (
                f'Create a Main EC institution-wide voter register “{name}” with '
                f'categor{"y" if len(categories) == 1 else "ies"} {category_names}. '
                'Assigned to Main EC elections only. '
                'The other Main EC member must approve before it can be used.'
            )
        else:
            summary = (
                f'Create a Sub EC voter register assigning voters to '
                f'{len(categories)} facult{"y" if len(categories) == 1 else "ies"}/department '
                f'container(s): {category_names}. '
                'The other Main EC member must approve before it can be used in elections.'
            )

        # Register creation requires dual Main EC approval before it becomes usable.
        try:
            decision = submit_main_ec_decision(
                user=request.user,
                decision_type=MainECDecision.TYPE_REGISTER_CREATE,
                title=f'Create voter register: {name}',
                summary=summary,
                payload={
                    'register_uuid': str(register.uuid),
                    'name': name,
                    'audience': audience,
                    'category': primary.name,
                    'category_uuids': [str(c.uuid) for c in categories],
                    'institution_category_uuids': institution_category_uuids,
                    'faculty_uuids': faculty_uuids,
                    'department_uuids': department_uuids,
                },
            )
        except GovernanceBlocked as exc:
            register.delete()
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)

        register.refresh_from_db()
        payload = VoterRegisterSerializer(register).data
        payload['primary_category'] = VoterCategorySerializer(primary).data
        payload['categories'] = VoterCategorySerializer(categories, many=True).data
        payload['decision'] = serialize_decision(decision)
        if register.approval_status == VoterRegister.APPROVAL_APPROVED:
            payload['message'] = 'Register created and approved.'
        else:
            payload['message'] = (
                'Register created and submitted for approval. The other Main EC '
                'member must approve it before it can be used in elections.'
            )
        return Response(payload, status=status.HTTP_201_CREATED)


class InstitutionRegisterDetailView(APIView):
    permission_classes = [IsMainEC]

    def get(self, request, register_uuid):
        try:
            register = _register_for_institution(request, register_uuid)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
        return Response(VoterRegisterSerializer(register).data)

    def patch(self, request, register_uuid):
        try:
            register = _register_for_institution(request, register_uuid)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
        serializer = VoterRegisterWriteSerializer(register, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(VoterRegisterSerializer(register).data)

    def delete(self, request, register_uuid):
        try:
            register = _register_for_institution(request, register_uuid)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
        from elections.models import Election
        Election.objects.filter(register=register).update(register=None)
        register.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InstitutionCategoryListCreateView(APIView):
    """Assign a faculty or department category (voter container) to a register."""
    permission_classes = [IsMainEC]

    def get(self, request, register_uuid):
        try:
            register = _register_for_institution(request, register_uuid)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
        qs = (
            VoterCategory.objects.filter(register=register)
            .select_related('faculty', 'department', 'department__faculty')
            .order_by('name')
        )
        return Response(VoterCategorySerializer(qs, many=True).data)

    def post(self, request, register_uuid):
        try:
            register = _register_for_institution(request, register_uuid)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)

        serializer = VoterCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        faculty_uuid = request.data.get('faculty_uuid')
        department_uuid = request.data.get('department_uuid')
        category_name = (request.data.get('name') or '').strip()

        if register.audience == VoterRegister.AUDIENCE_MAIN:
            if faculty_uuid or department_uuid:
                return Response(
                    {
                        'error': (
                            'This is a Main EC institution register. Add a preferred '
                            'category name instead of a faculty or department.'
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not category_name:
                return Response(
                    {'name': ['Enter a category name for this Main EC register.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif not faculty_uuid and not department_uuid and not category_name:
            return Response(
                {'error': 'Select a faculty, department, or provide a category name.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if faculty_uuid and VoterCategory.objects.filter(register=register, faculty__uuid=faculty_uuid).exists():
            return Response(
                {'faculty_uuid': ['This faculty is already assigned to the register.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if department_uuid and VoterCategory.objects.filter(register=register, department__uuid=department_uuid).exists():
            return Response(
                {'department_uuid': ['This department is already assigned to the register.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            register.audience == VoterRegister.AUDIENCE_MAIN
            and category_name
            and VoterCategory.objects.filter(register=register, name__iexact=category_name).exists()
        ):
            return Response(
                {'name': ['This category name already exists on the register.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        category = serializer.save(register=register)
        return Response(VoterCategorySerializer(category).data, status=status.HTTP_201_CREATED)


class InstitutionCategoryDetailView(APIView):
    permission_classes = [IsMainEC]

    def patch(self, request, register_uuid, category_uuid):
        try:
            register = _register_for_institution(request, register_uuid)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
        category = get_object_or_404(VoterCategory, uuid=category_uuid, register=register)
        serializer = VoterCategorySerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(VoterCategorySerializer(category).data)

    def delete(self, request, register_uuid, category_uuid):
        try:
            register = _register_for_institution(request, register_uuid)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)
        category = get_object_or_404(VoterCategory, uuid=category_uuid, register=register)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InstitutionRegisterEntryListView(generics.ListAPIView):
    permission_classes = [IsMainEC]
    serializer_class = VoterRegisterEntrySerializer

    def get_queryset(self):
        register = _register_for_institution(self.request, self.kwargs['register_uuid'])
        qs = (
            VoterRegisterEntry.objects.filter(register=register)
            .select_related('category', 'user', 'user__faculty', 'user__department')
            .order_by('voter_id')
        )
        category_uuid = self.request.query_params.get('category')
        if category_uuid:
            qs = qs.filter(category__uuid=category_uuid)
        search = (self.request.query_params.get('search') or '').strip()
        if search:
            qs = qs.filter(Q(voter_id__icontains=search) | Q(full_name__icontains=search))
        return qs


class InstitutionRegisterEntryUpdateView(APIView):
    """Propose an individual voter edit — requires dual Main EC approval."""
    permission_classes = [IsMainEC]

    def patch(self, request, register_uuid, entry_uuid):
        from accounts.governance import submit_main_ec_decision, decision_submitted_response
        from accounts.models import MainECDecision

        try:
            register = _register_for_institution(request, register_uuid)
            assert_institution_ready(request.user)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)

        if register.approval_status != VoterRegister.APPROVAL_APPROVED:
            return Response(
                {'error': 'Only approved registers can be edited voter-by-voter.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entry = get_object_or_404(VoterRegisterEntry, uuid=entry_uuid, register=register)
        voter_id = (request.data.get('voter_id') or entry.voter_id or '').strip()
        full_name = (request.data.get('full_name') or entry.full_name or '').strip()
        phone_number = (
            request.data.get('phone_number') if 'phone_number' in request.data else entry.phone_number
        ) or ''
        phone_number = str(phone_number).strip()

        if not voter_id or not full_name:
            return Response(
                {'error': 'Index number and full name are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        clash = (
            VoterRegisterEntry.objects.filter(register=register, voter_id__iexact=voter_id)
            .exclude(pk=entry.pk)
            .exists()
        )
        if clash:
            return Response(
                {'error': 'Another voter already uses this index on this register.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        before = {
            'voter_id': entry.voter_id,
            'full_name': entry.full_name,
            'phone_number': entry.phone_number or '',
        }
        after = {
            'voter_id': voter_id,
            'full_name': full_name,
            'phone_number': phone_number,
        }
        if before == after:
            return Response({'error': 'No changes detected.'}, status=status.HTTP_400_BAD_REQUEST)

        existing_pending = MainECDecision.objects.filter(
            status=MainECDecision.STATUS_PENDING,
            decision_type=MainECDecision.TYPE_REGISTER_ENTRY_UPDATE,
            payload__entry_uuid=str(entry.uuid),
        ).exists()
        if existing_pending:
            return Response(
                {
                    'error': (
                        'This voter already has a pending change awaiting dual Main EC approval. '
                        'Live data stays on the current values until that decision is enrolled.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        decision = submit_main_ec_decision(
            user=request.user,
            decision_type=MainECDecision.TYPE_REGISTER_ENTRY_UPDATE,
            title=f'Update voter {before["voter_id"]}',
            summary=(
                f'Change voter on “{register.name}”: '
                f'{before["voter_id"]} / {before["full_name"]} → '
                f'{after["voter_id"]} / {after["full_name"]} '
                f'(phone {after["phone_number"] or "—"}). '
                f'The other Main EC member must approve.'
            ),
            payload={
                'register_uuid': str(register.uuid),
                'entry_uuid': str(entry.uuid),
                **after,
                'before': before,
            },
        )
        return decision_submitted_response(decision)


class InstitutionRegisterImportView(APIView):
    permission_classes = [IsMainEC]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, register_uuid):
        try:
            register = _register_for_institution(request, register_uuid)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)

        category_uuid = request.data.get('category_uuid')
        file_obj = request.FILES.get('file')
        if not category_uuid:
            return Response({'error': 'category_uuid is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not file_obj:
            return Response({'error': 'CSV file is required'}, status=status.HTTP_400_BAD_REQUEST)

        category = get_object_or_404(VoterCategory, uuid=category_uuid, register=register)
        try:
            record = import_register_csv(
                register=register,
                category=category,
                file_obj=file_obj,
                imported_by=request.user,
            )
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                'uuid': str(record.uuid),
                'file_name': record.file_name,
                'rows_processed': record.rows_processed,
                'rows_created': record.rows_created,
                'errors': record.errors,
                'category': {
                    'uuid': str(category.uuid),
                    'name': category.name,
                    'scope_label': category.scope_label,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class InstitutionRegisterReplaceView(APIView):
    """
    Main EC: start a dual-approved voter re-upload for an approved register.

    Creates a staging register, submits TYPE_REGISTER_REPLACE, and returns
    staging category UUIDs so the CSV can be imported into staging. On dual
    approval, staging voters replace the live category and eligibility syncs
    for every election (Main EC + Sub EC) linked to the live register.
    """
    permission_classes = [IsMainEC]

    def post(self, request, register_uuid):
        import uuid as uuid_lib
        from django.db import transaction
        from accounts.governance import serialize_decision, submit_main_ec_decision
        from accounts.models import MainECDecision
        from elections.models import Election

        try:
            live = _register_for_institution(request, register_uuid)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)

        if live.replace_of_id:
            return Response(
                {'error': 'Cannot start a replace on a staging draft.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if live.approval_status != VoterRegister.APPROVAL_APPROVED:
            return Response(
                {'error': 'Only approved registers can be re-uploaded.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = live.pending_replacements.filter(
            approval_status=VoterRegister.APPROVAL_PENDING,
        ).first()
        if existing:
            return Response(
                {
                    'error': 'A re-upload is already awaiting the other Main EC member’s approval.',
                    'staging_uuid': str(existing.uuid),
                    'pending_replace': True,
                },
                status=status.HTTP_409_CONFLICT,
            )

        open_linked = Election.objects.filter(
            register=live,
            status__in=['open', 'paused'],
        ).exists()
        if open_linked:
            return Response(
                {
                    'error': (
                        'This register is linked to an open election. '
                        'Close or finish voting before replacing voters.'
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        category_uuid = request.data.get('category_uuid')
        if not category_uuid:
            return Response(
                {'error': 'category_uuid is required (which container to replace).'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        live_category = get_object_or_404(VoterCategory, uuid=category_uuid, register=live)

        try:
            assert_institution_ready(request.user)
        except GovernanceBlocked as exc:
            return Response({'error': str(exc), 'code': exc.code}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            staging = VoterRegister.objects.create(
                institution=live.institution,
                election=None,
                name=f'{live.name} · pending replace {uuid_lib.uuid4().hex[:8]}',
                description=f'Staging re-upload for {live.name}',
                audience=live.audience,
                replace_of=live,
                approval_status=VoterRegister.APPROVAL_PENDING,
                created_by=request.user,
            )
            category_map = {}
            staging_target = None
            for cat in live.categories.all():
                staged = VoterCategory.objects.create(
                    register=staging,
                    name=cat.name,
                    description=cat.description,
                    faculty=cat.faculty,
                    department=cat.department,
                )
                category_map[str(cat.uuid)] = str(staged.uuid)
                if cat.pk == live_category.pk:
                    staging_target = staged

            decision = submit_main_ec_decision(
                user=request.user,
                decision_type=MainECDecision.TYPE_REGISTER_REPLACE,
                title=f'Replace voters: {live.name}',
                summary=(
                    f'Replace voters in “{live_category.name}” on register “{live.name}". '
                    f'This will update eligibility for all elections using this register '
                    f'(Main EC and Sub EC). The other Main EC member must approve.'
                ),
                payload={
                    'live_register_uuid': str(live.uuid),
                    'staging_register_uuid': str(staging.uuid),
                    'target_live_category_uuid': str(live_category.uuid),
                    'target_staging_category_uuid': str(staging_target.uuid) if staging_target else None,
                    'category_map': category_map,
                    'register_name': live.name,
                    'category_name': live_category.name,
                },
            )

        live.refresh_from_db()
        return Response(
            {
                'message': (
                    'Re-upload submitted for dual Main EC approval. '
                    'Upload the CSV into the staging register, then wait for co-approval.'
                ),
                'live_register_uuid': str(live.uuid),
                'staging_register_uuid': str(staging.uuid),
                'target_live_category_uuid': str(live_category.uuid),
                'target_staging_category_uuid': str(staging_target.uuid) if staging_target else None,
                'category_map': category_map,
                'decision': serialize_decision(decision),
                'register': VoterRegisterSerializer(live).data,
            },
            status=status.HTTP_202_ACCEPTED,
        )
