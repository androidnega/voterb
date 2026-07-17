from .models import InAppNotification
from accounts.models import User
from elections.models import VoterEligibility

def create_notification(user, title, body, link='', notification_type='', metadata=None):
    """Create an in-app notification for a specific user."""
    InAppNotification.objects.create(
        user=user,
        title=title,
        body=body,
        link=link,
        notification_type=notification_type,
        metadata=metadata or {}
    )

def create_notification_for_users(user_ids, title, body, link='', notification_type='', metadata=None):
    """Create a notification for multiple users at once."""
    notifications = []
    for uid in user_ids:
        notifications.append(InAppNotification(
            user_id=uid,
            title=title,
            body=body,
            link=link,
            notification_type=notification_type,
            metadata=metadata or {}
        ))
    if notifications:
        InAppNotification.objects.bulk_create(notifications)

def notify_vote_cast(user, election_title, election_uuid):
    create_notification(
        user=user,
        title='✅ Vote Confirmed',
        body=f'Your vote in "{election_title}" has been recorded successfully.',
        link=f'/vote/{election_uuid}/confirmation',
        notification_type='vote_cast',
        metadata={'election_uuid': str(election_uuid)}
    )

def notify_election_opened(election):
    """Notify all eligible voters that an election is open."""
    eligible_user_ids = VoterEligibility.objects.filter(
        election=election,
        is_eligible=True
    ).values_list('user_id', flat=True)
    if eligible_user_ids:
        create_notification_for_users(
            user_ids=eligible_user_ids,
            title='🗳️ Election Opened',
            body=f'"{election.title}" is now open for voting. Cast your vote now!',
            link=f'/elections/{election.uuid}',
            notification_type='election_opened',
            metadata={'election_uuid': str(election.uuid)}
        )

def notify_election_closed(election):
    """Notify all eligible voters that an election has closed."""
    eligible_user_ids = VoterEligibility.objects.filter(
        election=election,
        is_eligible=True
    ).values_list('user_id', flat=True)
    if eligible_user_ids:
        create_notification_for_users(
            user_ids=eligible_user_ids,
            title='🔒 Election Closed',
            body=f'"{election.title}" has closed. Results will be available soon.',
            link=f'/elections/{election.uuid}',
            notification_type='election_closed',
            metadata={'election_uuid': str(election.uuid)}
        )

def notify_results_published(election):
    """Notify all students (eligible voters) that results are published."""
    # Get all students (or all users with role 'student' or 'candidate')
    student_user_ids = User.objects.filter(
        role__name__in=['student', 'candidate']
    ).values_list('id', flat=True)
    if student_user_ids:
        create_notification_for_users(
            user_ids=student_user_ids,
            title='📊 Results Published',
            body=f'Results for "{election.title}" have been published. View them now!',
            link=f'/results/{election.uuid}',
            notification_type='results_published',
            metadata={'election_uuid': str(election.uuid)}
        )

def notify_svt_requested(user, election):
    """Notify admins about an SVT request (security monitoring)."""
    admin_user_ids = User.objects.filter(
        role__name__in=['admin', 'super_admin']
    ).values_list('id', flat=True)
    if admin_user_ids:
        create_notification_for_users(
            user_ids=admin_user_ids,
            title='SVT Request',
            body=f'{user.email} requested an SVT for "{election.title}".',
            link=f'/elections/{election.uuid}',
            notification_type='svt_requested',
            metadata={'election_uuid': str(election.uuid), 'user_uuid': str(user.uuid)}
        )


def notify_svt_issued(user, election, *, expires_at=None, phone_masked=''):
    """Notify the voter that their SVT SMS was sent — with live expiry metadata."""
    minutes = 20
    try:
        from system.settings_utils import get_setting_int
        minutes = max(1, get_setting_int('svt_expiry_minutes', 20))
    except Exception:
        minutes = 20

    expires_iso = None
    if expires_at is not None:
        try:
            expires_iso = expires_at.isoformat()
        except Exception:
            expires_iso = str(expires_at)

    phone_bit = f' to {phone_masked}' if phone_masked else ''
    create_notification(
        user=user,
        title='Your Secure Voting Token was sent',
        body=(
            f'SVT sent by SMS{phone_bit} for "{election.title}". '
            f'Enter it within {minutes} minutes — one use only.'
        ),
        link=f'/vote/{election.uuid}',
        notification_type='svt_issued',
        metadata={
            'election_uuid': str(election.uuid),
            'expires_at': expires_iso,
            'countdown': True,
            'phone_masked': phone_masked or '',
        },
    )

def notify_fraud_alert(alert):
    """Notify admins about a new fraud alert."""
    admin_user_ids = User.objects.filter(
        role__name__in=['admin', 'super_admin']
    ).values_list('id', flat=True)
    if admin_user_ids:
        create_notification_for_users(
            user_ids=admin_user_ids,
            title='⚠️ Fraud Alert',
            body=alert.description[:200],
            link=f'/fraud/alerts/{alert.uuid}',
            notification_type='fraud_alert',
            metadata={'alert_uuid': str(alert.uuid)}
        )


def _decision_uuid(decision) -> str:
    return str(decision.uuid)


def resolve_main_ec_approval_notifications(decision):
    """Mark pending approval alerts for this decision as read (request is resolved)."""
    du = _decision_uuid(decision)
    InAppNotification.objects.filter(
        notification_type='main_ec_approval',
        is_read=False,
        metadata__decision_uuid=du,
    ).update(is_read=True)


def notify_main_ec_approval_needed(decision, exclude_user_ids=None):
    """Notify co–Main EC members that a decision awaits their approval.

    At most one unread approval notification per user per decision while pending.
    """
    from accounts.governance import main_ec_member_user_ids

    exclude = set(exclude_user_ids or [])
    # Proposer / anyone who already signed should not get another "please approve" ping.
    exclude |= set(decision.approvals.values_list('user_id', flat=True))
    recipient_ids = [
        uid for uid in main_ec_member_user_ids(decision.institution)
        if uid not in exclude
    ]
    if not recipient_ids:
        return

    du = _decision_uuid(decision)
    proposer_name = (
        f'{decision.proposed_by.first_name or ""} {decision.proposed_by.last_name or ""}'.strip()
        or decision.proposed_by.email
    )
    title = 'Approval required'
    body = (
        f'{proposer_name} submitted "{decision.title}". '
        'Your co-signature is needed before enrollment.'
    )
    metadata = {
        'decision_uuid': du,
        'decision_type': decision.decision_type,
    }

    to_create = []
    for uid in recipient_ids:
        already = InAppNotification.objects.filter(
            user_id=uid,
            notification_type='main_ec_approval',
            metadata__decision_uuid=du,
        ).exists()
        if already:
            continue
        to_create.append(InAppNotification(
            user_id=uid,
            title=title,
            body=body,
            link='/approvals',
            notification_type='main_ec_approval',
            metadata=metadata,
        ))
    if to_create:
        InAppNotification.objects.bulk_create(to_create)


def notify_main_ec_decision_enrolled(decision):
    """Notify Main EC members that a dual-approved decision is enrolled."""
    from accounts.governance import main_ec_member_user_ids

    resolve_main_ec_approval_notifications(decision)

    recipient_ids = list(main_ec_member_user_ids(decision.institution))
    if not recipient_ids:
        return
    du = _decision_uuid(decision)
    body = f'"{decision.title}" was approved by both Main ECs and is now enrolled.'
    metadata = {
        'decision_uuid': du,
        'decision_type': decision.decision_type,
    }
    # One enrolled notice per user per decision (avoid double-chime on retries).
    to_create = []
    for uid in recipient_ids:
        if InAppNotification.objects.filter(
            user_id=uid,
            notification_type='main_ec_enrolled',
            metadata__decision_uuid=du,
        ).exists():
            continue
        to_create.append(InAppNotification(
            user_id=uid,
            title='Decision enrolled',
            body=body,
            link='/approvals',
            notification_type='main_ec_enrolled',
            metadata=metadata,
        ))
    if to_create:
        InAppNotification.objects.bulk_create(to_create)


def notify_main_ec_decision_rejected(decision):
    """Notify the proposer (and other Main ECs) that a decision was rejected."""
    from accounts.governance import main_ec_member_user_ids

    resolve_main_ec_approval_notifications(decision)

    recipient_ids = list(main_ec_member_user_ids(decision.institution))
    if not recipient_ids:
        return
    du = _decision_uuid(decision)
    rejector = decision.rejected_by
    rejector_name = ''
    if rejector:
        rejector_name = (
            f'{rejector.first_name or ""} {rejector.last_name or ""}'.strip()
            or rejector.email
        )
    reason = (decision.rejection_reason or '').strip()
    body = f'"{decision.title}" was rejected'
    if rejector_name:
        body += f' by {rejector_name}'
    if reason:
        body += f': {reason}'
    else:
        body += '.'

    metadata = {
        'decision_uuid': du,
        'decision_type': decision.decision_type,
    }
    truncated = body[:400]
    to_create = []
    for uid in recipient_ids:
        if InAppNotification.objects.filter(
            user_id=uid,
            notification_type='main_ec_rejected',
            metadata__decision_uuid=du,
        ).exists():
            continue
        to_create.append(InAppNotification(
            user_id=uid,
            title='Decision rejected',
            body=truncated,
            link='/approvals',
            notification_type='main_ec_rejected',
            metadata=metadata,
        ))
    if to_create:
        InAppNotification.objects.bulk_create(to_create)
