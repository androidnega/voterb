"""Dual Main EC governance — minimum 2 ECs, both must approve before enrollment."""

from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from accounts.models import (
    ECMembership,
    ECUnit,
    MainECDecision,
    MainECDecisionApproval,
    Role,
    SubECAssignment,
    User,
)
from accounts.org import user_is_main_ec
from system.models import InstitutionProfile

REQUIRED_MAIN_EC_COUNT = 2


class GovernanceBlocked(Exception):
    def __init__(self, message, code='governance_blocked'):
        super().__init__(message)
        self.code = code


def resolve_user_institution(user) -> InstitutionProfile | None:
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if user.institution_id:
        return user.institution
    membership = (
        ECMembership.objects.filter(
            user=user,
            is_active=True,
            ec_unit__is_active=True,
            ec_unit__unit_type=ECUnit.UNIT_MAIN,
        )
        .select_related('ec_unit__institution')
        .first()
    )
    if membership:
        return membership.ec_unit.institution
    return None


def main_ec_member_count(institution: InstitutionProfile) -> int:
    return ECMembership.objects.filter(
        ec_unit__institution=institution,
        ec_unit__unit_type=ECUnit.UNIT_MAIN,
        ec_unit__is_active=True,
        is_active=True,
    ).count()


def main_ec_member_user_ids(institution: InstitutionProfile) -> set:
    return set(
        ECMembership.objects.filter(
            ec_unit__institution=institution,
            ec_unit__unit_type=ECUnit.UNIT_MAIN,
            ec_unit__is_active=True,
            is_active=True,
        ).values_list('user_id', flat=True)
    )


def institution_ready_for_operations(institution: InstitutionProfile) -> bool:
    return main_ec_member_count(institution) >= REQUIRED_MAIN_EC_COUNT


def institution_governance_status(institution: InstitutionProfile | None) -> dict:
    if not institution:
        return {
            'ready': False,
            'main_ec_count': 0,
            'required_main_ec_count': REQUIRED_MAIN_EC_COUNT,
            'dual_approval_required': True,
            'message': 'No institution linked to this account.',
        }
    count = main_ec_member_count(institution)
    ready = count >= REQUIRED_MAIN_EC_COUNT
    if ready:
        message = (
            'Institution is operational. All Main EC decisions require approval '
            f'from both institutional EC members before enrollment.'
        )
    else:
        needed = REQUIRED_MAIN_EC_COUNT - count
        message = (
            f'Add {needed} more Main EC member(s) before this institution can '
            'run elections or enroll decisions.'
        )
    return {
        'ready': ready,
        'main_ec_count': count,
        'required_main_ec_count': REQUIRED_MAIN_EC_COUNT,
        'dual_approval_required': True,
        'message': message,
    }


def governance_applies_to_user(user) -> bool:
    """True only for institutional Main EC users."""
    return user_is_main_ec(user)


def assert_institution_ready(user):
    institution = resolve_user_institution(user)
    if not institution:
        raise GovernanceBlocked(
            'Your account is not linked to an institution. Contact the Super Admin.',
            code='no_institution',
        )
    if not institution_ready_for_operations(institution):
        status = institution_governance_status(institution)
        raise GovernanceBlocked(status['message'], code='insufficient_main_ec')
    return institution


def user_is_main_ec_of_institution(user, institution: InstitutionProfile) -> bool:
    return user.id in main_ec_member_user_ids(institution)


def serialize_decision(decision: MainECDecision) -> dict:
    approvals = list(
        decision.approvals.select_related('user').order_by('approved_at')
    )
    main_ids = main_ec_member_user_ids(decision.institution)
    payload = dict(decision.payload or {})
    if decision.decision_type in (
        MainECDecision.TYPE_SUB_EC_CREATE,
        MainECDecision.TYPE_SUB_EC_UPDATE,
    ):
        sub_ec = dict(payload.get('sub_ec') or {})
        sub_ec.pop('password_hash', None)
        payload['sub_ec'] = sub_ec
    return {
        'uuid': str(decision.uuid),
        'decision_type': decision.decision_type,
        'title': decision.title,
        'summary': decision.summary,
        'status': decision.status,
        'payload': payload,
        'result_ref': decision.result_ref,
        'proposed_by': {
            'uuid': str(decision.proposed_by.uuid),
            'email': decision.proposed_by.email,
            'name': f'{decision.proposed_by.first_name or ""} {decision.proposed_by.last_name or ""}'.strip(),
        },
        'approvals': [
            {
                'uuid': str(a.uuid),
                'user_uuid': str(a.user.uuid),
                'email': a.user.email,
                'name': f'{a.user.first_name or ""} {a.user.last_name or ""}'.strip(),
                'approved_at': a.approved_at.isoformat(),
            }
            for a in approvals
        ],
        'approvals_required': REQUIRED_MAIN_EC_COUNT,
        'approvals_received': len(approvals),
        'can_approve': decision.status == MainECDecision.STATUS_PENDING,
        'enrolled_at': decision.enrolled_at.isoformat() if decision.enrolled_at else None,
        'created_at': decision.created_at.isoformat(),
        'rejection_reason': decision.rejection_reason,
    }


@transaction.atomic
def submit_main_ec_decision(
    *,
    user: User,
    decision_type: str,
    title: str,
    summary: str = '',
    payload: dict | None = None,
) -> MainECDecision:
    institution = assert_institution_ready(user)
    decision = MainECDecision.objects.create(
        institution=institution,
        decision_type=decision_type,
        title=title,
        summary=summary,
        payload=payload or {},
        proposed_by=user,
        status=MainECDecision.STATUS_PENDING,
    )
    # Proposer counts as the first approval; co-Main EC must still co-sign.
    MainECDecisionApproval.objects.get_or_create(
        decision=decision,
        user=user,
        defaults={'note': 'Proposed'},
    )
    decision = try_enroll_decision(decision)
    # Notify after commit so a notification failure never rolls back the proposal.
    _schedule_decision_notification(decision, exclude_user_ids={user.id})
    return decision


def _schedule_decision_notification(decision: MainECDecision, exclude_user_ids=None):
    decision_pk = decision.pk
    status = decision.status
    exclude = set(exclude_user_ids or [])

    def _notify():
        try:
            from notifications.services import (
                notify_main_ec_approval_needed,
                notify_main_ec_decision_enrolled,
            )

            refreshed = MainECDecision.objects.get(pk=decision_pk)
            if status == MainECDecision.STATUS_PENDING and refreshed.status == MainECDecision.STATUS_PENDING:
                notify_main_ec_approval_needed(refreshed, exclude_user_ids=exclude)
            elif status == MainECDecision.STATUS_ENROLLED or refreshed.status == MainECDecision.STATUS_ENROLLED:
                notify_main_ec_decision_enrolled(refreshed)
        except Exception:
            pass

    transaction.on_commit(_notify)


@transaction.atomic
def approve_main_ec_decision(decision: MainECDecision, user: User, note: str = '') -> MainECDecision:
    # Serialize concurrent approvals and make retries safe. A proxy can return
    # 502 after enrollment has committed, so the same signer may legitimately
    # retry the versioned endpoint.
    decision = MainECDecision.objects.select_for_update().get(pk=decision.pk)
    if (
        decision.status == MainECDecision.STATUS_ENROLLED
        and decision.approvals.filter(user=user).exists()
    ):
        return decision
    if decision.status != MainECDecision.STATUS_PENDING:
        raise GovernanceBlocked('This decision is no longer pending approval.', code='not_pending')
    if not user_is_main_ec_of_institution(user, decision.institution):
        raise GovernanceBlocked('Only Main EC members of this institution can approve.', code='forbidden')

    MainECDecisionApproval.objects.get_or_create(
        decision=decision,
        user=user,
        defaults={'note': note or ''},
    )
    decision = try_enroll_decision(decision)
    if decision.status == MainECDecision.STATUS_ENROLLED:
        _schedule_decision_notification(decision)
    return decision


@transaction.atomic
def reject_main_ec_decision(decision: MainECDecision, user: User, reason: str = '') -> MainECDecision:
    if decision.status != MainECDecision.STATUS_PENDING:
        raise GovernanceBlocked('This decision is no longer pending.', code='not_pending')
    if not user_is_main_ec_of_institution(user, decision.institution):
        raise GovernanceBlocked('Only Main EC members of this institution can reject.', code='forbidden')
    decision.status = MainECDecision.STATUS_REJECTED
    decision.rejected_by = user
    decision.rejection_reason = reason or 'Rejected by Main EC member.'
    decision.save(update_fields=['status', 'rejected_by', 'rejection_reason', 'updated_at'])

    if decision.decision_type == MainECDecision.TYPE_REGISTER_CREATE:
        from elections.models import VoterRegister

        register_uuid = (decision.payload or {}).get('register_uuid')
        if register_uuid:
            VoterRegister.objects.filter(uuid=register_uuid).update(
                approval_status=VoterRegister.APPROVAL_REJECTED,
            )

    if decision.decision_type == MainECDecision.TYPE_REGISTER_REPLACE:
        from elections.models import VoterRegister

        staging_uuid = (decision.payload or {}).get('staging_register_uuid')
        if staging_uuid:
            VoterRegister.objects.filter(uuid=staging_uuid).delete()

    from notifications.services import notify_main_ec_decision_rejected

    decision_pk = decision.pk

    def _notify_rejected():
        try:
            refreshed = MainECDecision.objects.get(pk=decision_pk)
            notify_main_ec_decision_rejected(refreshed)
        except Exception:
            pass

    transaction.on_commit(_notify_rejected)
    return decision


def _approval_count_met(decision: MainECDecision) -> bool:
    main_ids = main_ec_member_user_ids(decision.institution)
    if len(main_ids) < REQUIRED_MAIN_EC_COUNT:
        return False
    approved_ids = set(decision.approvals.values_list('user_id', flat=True))
    valid = approved_ids & main_ids
    # Dual approval: at least two distinct Main EC members must approve.
    return len(valid) >= REQUIRED_MAIN_EC_COUNT


@transaction.atomic
def try_enroll_decision(decision: MainECDecision) -> MainECDecision:
    decision.refresh_from_db()
    if decision.status != MainECDecision.STATUS_PENDING:
        return decision
    if not _approval_count_met(decision):
        return decision

    result_ref = _execute_decision(decision)
    decision.status = MainECDecision.STATUS_ENROLLED
    decision.result_ref = result_ref or decision.result_ref
    decision.enrolled_at = timezone.now()
    decision.save(update_fields=['status', 'result_ref', 'enrolled_at', 'updated_at'])
    return decision


def decision_submitted_response(decision: MainECDecision):
    from rest_framework import status
    from rest_framework.response import Response

    data = serialize_decision(decision)
    if decision.status == MainECDecision.STATUS_ENROLLED:
        data['message'] = 'Decision enrolled — both Main EC members approved.'
    else:
        data['message'] = (
            'Submitted for dual Main EC approval. Your approval is recorded; '
            'the other institutional EC member must also approve before enrollment.'
        )
    return Response(data, status=status.HTTP_202_ACCEPTED)


def _execute_decision(decision: MainECDecision) -> str:
    from django.shortcuts import get_object_or_404
    from elections.models import Election
    from elections.serializers import ElectionCreateUpdateSerializer
    from elections.services.deletion import delete_election
    from elections.services.register_service import sync_eligibility_from_registers

    payload = decision.payload or {}
    proposer = decision.proposed_by

    if decision.decision_type == MainECDecision.TYPE_ELECTION_CREATE:
        serializer = ElectionCreateUpdateSerializer(
            data=payload.get('election', {}),
            context={'request': type('R', (), {'user': proposer})()},
        )
        serializer.is_valid(raise_exception=True)
        from system.models import InstitutionProfile

        owner_kwargs = {
            'owner_type': payload.get('owner_type') or Election.OWNER_MAIN,
        }
        inst_uuid = payload.get('institution_uuid')
        unit_uuid = payload.get('owner_ec_unit_uuid')
        if inst_uuid:
            owner_kwargs['institution'] = InstitutionProfile.objects.filter(uuid=inst_uuid).first()
        if unit_uuid:
            owner_kwargs['owner_ec_unit'] = ECUnit.objects.filter(uuid=unit_uuid).first()
        if not owner_kwargs.get('institution'):
            owner_kwargs['institution'] = resolve_user_institution(proposer)
        election = serializer.save(created_by=proposer, **owner_kwargs)
        return str(election.uuid)

    if decision.decision_type == MainECDecision.TYPE_ELECTION_UPDATE:
        election = get_object_or_404(Election, uuid=payload['election_uuid'])
        if election.status in ('open', 'paused', 'closed', 'archived'):
            raise GovernanceBlocked(
                'This election has started. Editing is locked.',
                code='election_locked',
            )
        serializer = ElectionCreateUpdateSerializer(election, data=payload.get('election', {}), partial=True)
        serializer.is_valid(raise_exception=True)
        election = serializer.save()
        return str(election.uuid)

    if decision.decision_type == MainECDecision.TYPE_ELECTION_OPEN:
        election = get_object_or_404(Election, uuid=payload['election_uuid'])
        if election.status == 'open':
            return str(election.uuid)
        if election.status not in ('draft', 'scheduled'):
            raise GovernanceBlocked(
                'Election must be draft or scheduled before opening.',
                code='invalid_state',
            )
        if election.status == 'draft':
            election.status = 'scheduled'
            election.save(update_fields=['status', 'updated_at'])
        sync_eligibility_from_registers(election, verified_by=proposer)
        election.status = 'open'
        election.save(update_fields=['status', 'updated_at'])
        return str(election.uuid)

    if decision.decision_type == MainECDecision.TYPE_ELECTION_CLOSE:
        election = get_object_or_404(Election, uuid=payload['election_uuid'])
        # Idempotent: election may already be closed (e.g. peer closed via Sub EC
        # path, or end-of-window close) while this dual-approval was still pending.
        if election.status in ('closed', 'archived'):
            return str(election.uuid)
        if election.status not in ('open', 'paused'):
            raise GovernanceBlocked(
                f'Election cannot be closed from status "{election.status}".',
                code='invalid_state',
            )
        election.status = 'closed'
        election.save(update_fields=['status', 'updated_at'])
        return str(election.uuid)

    if decision.decision_type == MainECDecision.TYPE_ELECTION_DELETE:
        election = get_object_or_404(Election, uuid=payload['election_uuid'])
        if election.status in ('open', 'paused', 'closed', 'archived'):
            raise GovernanceBlocked(
                'This election has started. Deletion is locked.',
                code='election_locked',
            )
        election_uuid = str(election.uuid)
        delete_election(election)
        return election_uuid

    if decision.decision_type == MainECDecision.TYPE_REGISTER_CREATE:
        from elections.models import VoterRegister

        register = get_object_or_404(VoterRegister, uuid=payload['register_uuid'])
        register.approval_status = VoterRegister.APPROVAL_APPROVED
        register.approved_at = timezone.now()
        register.save(update_fields=['approval_status', 'approved_at'])
        return str(register.uuid)

    if decision.decision_type == MainECDecision.TYPE_REGISTER_REPLACE:
        from elections.models import VoterRegister
        from elections.services.register_service import apply_register_replace

        live = get_object_or_404(VoterRegister, uuid=payload['live_register_uuid'])
        staging = get_object_or_404(VoterRegister, uuid=payload['staging_register_uuid'])
        apply_register_replace(
            live_register=live,
            staging_register=staging,
            target_category_uuid=payload.get('target_live_category_uuid'),
            verified_by=proposer,
        )
        return str(live.uuid)

    if decision.decision_type == MainECDecision.TYPE_REGISTER_ENTRY_UPDATE:
        from elections.models import VoterRegisterEntry
        from elections.services.register_service import (
            ensure_register_entry_users,
            sync_elections_for_register,
        )
        from elections.services.eligibility import resolve_or_create_voter

        entry = get_object_or_404(VoterRegisterEntry, uuid=payload['entry_uuid'])
        voter_id = (payload.get('voter_id') or entry.voter_id or '').strip()
        full_name = (payload.get('full_name') or entry.full_name or '').strip()
        phone_number = (payload.get('phone_number') or '').strip()
        if not voter_id or not full_name:
            raise GovernanceBlocked('Voter index and full name are required.', code='invalid_entry')

        # Prevent colliding with another entry on the same register
        clash = (
            VoterRegisterEntry.objects.filter(register=entry.register, voter_id__iexact=voter_id)
            .exclude(pk=entry.pk)
            .exists()
        )
        if clash:
            raise GovernanceBlocked('Another voter already uses this index on this register.', code='duplicate_index')

        entry.voter_id = voter_id
        entry.full_name = full_name
        entry.phone_number = phone_number
        entry.save(update_fields=['voter_id', 'full_name', 'phone_number'])

        user = entry.user
        if not user:
            user, _err = resolve_or_create_voter(voter_id)
            if user:
                entry.user = user
                entry.save(update_fields=['user'])

        if user:
            parts = full_name.split(None, 1)
            user.index_number = voter_id
            user.first_name = parts[0][:150] if parts else user.first_name
            user.last_name = parts[1][:150] if len(parts) > 1 else ''
            if phone_number:
                user.phone_number = phone_number
            user.save(update_fields=['index_number', 'first_name', 'last_name', 'phone_number'])

        # Propagate into every election sharing this live institutional register.
        ensure_register_entry_users(entry.register)
        sync_elections_for_register(entry.register, verified_by=proposer)
        return str(entry.uuid)

    if decision.decision_type == MainECDecision.TYPE_SUB_EC_CREATE:
        from django.contrib.auth.hashers import identify_hasher
        from elections.models import Department, Faculty

        sub_data = payload.get('sub_ec', {})
        parent = (
            ECUnit.objects.filter(
                institution=decision.institution,
                unit_type=ECUnit.UNIT_MAIN,
                is_active=True,
            )
            .order_by('created_at')
            .first()
        )
        if not parent:
            raise GovernanceBlocked('Institution Main EC unit was not found.', code='no_main_ec_unit')

        email = (sub_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise GovernanceBlocked('A user with this Sub EC email already exists.', code='duplicate_email')

        unit_name = (sub_data.get('unit_name') or '').strip()
        if ECUnit.objects.filter(institution=decision.institution, name__iexact=unit_name).exists():
            raise GovernanceBlocked('An EC unit with this name already exists.', code='duplicate_unit')

        role, _ = Role.objects.get_or_create(
            name='sub_ec',
            defaults={'description': 'Sub Electoral Commission (faculty/department)'},
        )
        password_hash = sub_data.get('password_hash') or ''
        identify_hasher(password_hash)
        user = User.objects.create(
            email=email,
            first_name=(sub_data.get('first_name') or '').strip(),
            last_name=(sub_data.get('last_name') or '').strip(),
            phone_number=(sub_data.get('phone_number') or '').strip() or None,
            password=password_hash,
            role=role,
            institution=decision.institution,
            is_staff=True,
            is_verified=True,
            is_active=True,
        )
        unit = ECUnit.objects.create(
            institution=decision.institution,
            unit_type=ECUnit.UNIT_SUB,
            name=unit_name,
            parent=parent,
            is_active=True,
        )
        ECMembership.objects.create(
            user=user,
            ec_unit=unit,
            is_active=True,
        )

        faculty_ids = sub_data.get('faculty_uuids') or []
        department_ids = sub_data.get('department_uuids') or []
        assignments = [
            SubECAssignment(ec_unit=unit, faculty=faculty)
            for faculty in Faculty.objects.filter(uuid__in=faculty_ids)
        ]
        assignments.extend(
            SubECAssignment(ec_unit=unit, department=department)
            for department in Department.objects.filter(uuid__in=department_ids)
        )
        if assignments:
            SubECAssignment.objects.bulk_create(assignments)
        return str(unit.uuid)

    if decision.decision_type == MainECDecision.TYPE_SUB_EC_UPDATE:
        from django.contrib.auth.hashers import identify_hasher
        from elections.models import Department, Faculty

        unit_uuid = payload.get('unit_uuid')
        unit = get_object_or_404(
            ECUnit,
            uuid=unit_uuid,
            institution=decision.institution,
            unit_type=ECUnit.UNIT_SUB,
        )
        sub_data = payload.get('sub_ec') or {}

        unit_name = (sub_data.get('unit_name') or unit.name).strip()
        if (
            unit_name
            and ECUnit.objects.filter(institution=decision.institution, name__iexact=unit_name)
            .exclude(uuid=unit.uuid)
            .exists()
        ):
            raise GovernanceBlocked('An EC unit with this name already exists.', code='duplicate_unit')

        unit.name = unit_name or unit.name
        if 'is_active' in sub_data:
            unit.is_active = bool(sub_data.get('is_active'))
        unit.save(update_fields=['name', 'is_active', 'updated_at'])

        membership = (
            ECMembership.objects.filter(ec_unit=unit, is_active=True)
            .select_related('user')
            .order_by('created_at')
            .first()
        )
        if membership:
            user = membership.user
            email = (sub_data.get('email') or user.email or '').strip().lower()
            if email and User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                raise GovernanceBlocked('A user with this Sub EC email already exists.', code='duplicate_email')
            user.email = email or user.email
            user.first_name = (sub_data.get('first_name') if 'first_name' in sub_data else user.first_name) or ''
            user.last_name = (sub_data.get('last_name') if 'last_name' in sub_data else user.last_name) or ''
            if 'phone_number' in sub_data:
                user.phone_number = (sub_data.get('phone_number') or '').strip() or None
            password_hash = sub_data.get('password_hash') or ''
            if password_hash:
                identify_hasher(password_hash)
                user.password = password_hash
            user.save()

        # Replace faculty/department assignments when provided
        if 'faculty_uuids' in sub_data or 'department_uuids' in sub_data:
            faculty_ids = sub_data.get('faculty_uuids') or []
            department_ids = sub_data.get('department_uuids') or []
            SubECAssignment.objects.filter(ec_unit=unit).delete()
            assignments = [
                SubECAssignment(ec_unit=unit, faculty=faculty)
                for faculty in Faculty.objects.filter(uuid__in=faculty_ids)
            ]
            assignments.extend(
                SubECAssignment(ec_unit=unit, department=department)
                for department in Department.objects.filter(uuid__in=department_ids)
            )
            if assignments:
                SubECAssignment.objects.bulk_create(assignments)

        return str(unit.uuid)

    raise GovernanceBlocked(f'Unsupported decision type: {decision.decision_type}', code='unsupported')
