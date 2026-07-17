from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import MFALog, User
from accounts.permissions import IsElectionViewer, IsSuperAdmin
from candidates.models import Candidate
from elections.models import Department, Election, Faculty, VoterEligibility
from system.models import FeatureFlag, MaintenanceState
from voting.models import Vote


ROLE_LABELS = {
    'admin': 'Main EC',
    'sub_ec': 'Sub EC',
    'super_admin': 'Platform Governance',
    'auditor': 'Auditor',
    'student': 'Student',
    'candidate': 'Candidate',
}


def _display_name(user):
    parts = [user.first_name, user.last_name]
    name = ' '.join(p for p in parts if p).strip()
    if name:
        return name
    if user.email:
        return user.email.split('@')[0]
    if user.index_number:
        return user.index_number
    return 'User'


def _greeting():
    hour = timezone.now().hour
    if hour < 12:
        return 'morning'
    if hour < 18:
        return 'afternoon'
    return 'evening'


def _role_name(user):
    if user.is_superuser:
        return 'super_admin'
    if user.role_id and user.role:
        return user.role.name
    if user.is_staff:
        return 'admin'
    if user.index_number:
        return 'student'
    return ''


class AdminDashboardView(APIView):
    permission_classes = [IsElectionViewer]

    def get(self, request):
        from elections.services.ec_access import elections_visible_to

        visible = elections_visible_to(request.user)
        total_elections = visible.count()
        active_elections = visible.filter(status='open').count()
        scheduled_elections = visible.filter(status='scheduled').count()
        closed_elections = visible.filter(status__in=['closed', 'archived']).count()
        total_voters = User.objects.filter(role__name='student').count()
        visible_ids = list(visible.values_list('id', flat=True))
        total_votes = Vote.objects.filter(election_id__in=visible_ids).count() if visible_ids else 0
        unique_voters = (
            Vote.objects.filter(election_id__in=visible_ids).values('user').distinct().count()
            if visible_ids else 0
        )
        total_candidates = (
            Candidate.objects.filter(election_id__in=visible_ids, status='approved').count()
            if visible_ids else 0
        )
        eligible_voters = (
            VoterEligibility.objects.filter(election_id__in=visible_ids, is_eligible=True).count()
            if visible_ids else 0
        )

        turnout_pct = 0
        if eligible_voters > 0:
            turnout_pct = round((unique_voters / eligible_voters) * 100, 1)

        cutoff = timezone.now() - timedelta(days=7)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        votes_today = (
            Vote.objects.filter(election_id__in=visible_ids, timestamp__gte=today_start).count()
            if visible_ids else 0
        )
        mfa_logs = MFALog.objects.filter(created_at__gte=cutoff).order_by('-created_at')[:5]
        activities = []
        for log in mfa_logs:
            actor = (log.user.email if log.user and log.user.email else None) or (
                log.user.index_number if log.user else 'Unknown'
            )
            activities.append({
                'type': self._activity_type(log.event_type),
                'icon': self._get_icon(log.event_type),
                'message': f"{actor} — {log.event_type.replace('_', ' ')}",
                'time': log.created_at.strftime('%b %d, %I:%M %p'),
            })

        chart_dates = []
        chart_counts = []
        for i in range(6, -1, -1):
            day = timezone.now() - timedelta(days=i)
            start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            count = (
                Vote.objects.filter(
                    election_id__in=visible_ids,
                    timestamp__gte=start,
                    timestamp__lt=end,
                ).count()
                if visible_ids else 0
            )
            chart_dates.append(day.strftime('%a'))
            chart_counts.append(count)

        status_labels = []
        status_values = []
        for status, label in [
            ('open', 'Open'),
            ('scheduled', 'Scheduled'),
            ('closed', 'Closed'),
            ('draft', 'Draft'),
            ('paused', 'Paused'),
        ]:
            count = visible.filter(status=status).count()
            if count > 0:
                status_labels.append(label)
                status_values.append(count)

        live_elections = []
        for election in visible.filter(status__in=['open', 'scheduled', 'paused']).order_by('-start_date')[:6]:
            eligible = election.eligibilities.filter(is_eligible=True).count()
            voters = Vote.objects.filter(election=election).values('user').distinct().count()
            votes = Vote.objects.filter(election=election).count()
            election_turnout = round((voters / eligible) * 100, 1) if eligible else 0
            live_elections.append({
                'uuid': str(election.uuid),
                'title': election.title,
                'status': election.status,
                'eligible_voters': eligible,
                'votes_cast': votes,
                'unique_voters': voters,
                'turnout': election_turnout,
                'candidates': Candidate.objects.filter(election=election, status='approved').count(),
            })

        return Response({
            'context': {
                'display_name': _display_name(request.user),
                'role_name': _role_name(request.user),
                'role_label': ROLE_LABELS.get(_role_name(request.user), 'Administrator'),
                'greeting': _greeting(),
                'today_date': timezone.now().strftime('%A, %B %d, %Y'),
            },
            'stats': {
                'total_elections': total_elections,
                'active_elections': active_elections,
                'scheduled_elections': scheduled_elections,
                'closed_elections': closed_elections,
                'total_voters': total_voters,
                'eligible_voters': eligible_voters,
                'unique_voters': unique_voters,
                'total_votes': total_votes,
                'total_candidates': total_candidates,
                'turnout': turnout_pct,
                'votes_today': votes_today,
            },
            'recent_activities': activities,
            'chart_data': {
                'labels': chart_dates,
                'values': chart_counts,
            },
            'status_breakdown': {
                'labels': status_labels,
                'values': status_values,
            },
            'live_elections': live_elections,
        })

    def _activity_type(self, event_type):
        if 'login' in event_type or 'otp' in event_type:
            return 'login'
        if 'vote' in event_type:
            return 'vote'
        if 'election' in event_type:
            return 'election'
        return 'other'

    def _get_icon(self, event_type):
        if 'login' in event_type:
            return 'fas fa-sign-in-alt'
        elif 'vote' in event_type:
            return 'fas fa-check-circle'
        elif 'otp' in event_type:
            return 'fas fa-shield-alt'
        elif 'election' in event_type:
            return 'fas fa-calendar-check'
        return 'fas fa-info-circle'


class SuperAdminDashboardView(APIView):
    """Platform governance dashboard — no election or voting metrics."""

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        total_users = User.objects.count()
        staff_users = User.objects.filter(role__name__in=['admin', 'super_admin', 'auditor']).count()
        student_users = User.objects.filter(role__name='student').count()
        active_users = User.objects.filter(is_active=True).count()

        role_rows = (
            User.objects.exclude(role__isnull=True)
            .values('role__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        role_labels = []
        role_values = []
        for row in role_rows:
            name = row['role__name'] or 'unknown'
            role_labels.append(ROLE_LABELS.get(name, name.replace('_', ' ').title()))
            role_values.append(row['count'])

        month_labels = []
        user_series = []
        cumulative_users = []
        user_rows = (
            User.objects.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        user_map = {row['month'].strftime('%b %Y'): row['count'] for row in user_rows if row['month']}

        anchor = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        months = []
        cursor = anchor
        for _ in range(7):
            months.insert(0, cursor)
            cursor = (cursor - timedelta(days=1)).replace(day=1)

        for month_start in months:
            label = month_start.strftime('%b')
            key = month_start.strftime('%b %Y')
            month_labels.append(label)
            user_series.append(user_map.get(key, 0))
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            cumulative_users.append(User.objects.filter(created_at__lt=month_end).count())

        flags = FeatureFlag.objects.all()
        flags_enabled = flags.filter(is_enabled=True).count()
        flags_total = flags.count()
        maintenance = MaintenanceState.objects.first()
        maintenance_active = bool(maintenance and maintenance.is_active)

        cutoff = timezone.now() - timedelta(days=7)
        mfa_logs = MFALog.objects.filter(created_at__gte=cutoff).order_by('-created_at')[:10]
        activities = []
        for log in mfa_logs:
            actor = (log.user.email if log.user and log.user.email else None) or (
                log.user.index_number if log.user else 'Unknown'
            )
            activities.append({
                'type': 'login' if 'login' in log.event_type or 'otp' in log.event_type else 'other',
                'icon': 'fas fa-shield-alt' if 'otp' in log.event_type else 'fas fa-sign-in-alt',
                'message': f"{actor} — {log.event_type.replace('_', ' ')}",
                'time': log.created_at.strftime('%b %d, %I:%M %p'),
            })

        return Response({
            'context': {
                'display_name': _display_name(request.user),
                'role_name': _role_name(request.user),
                'role_label': ROLE_LABELS.get(_role_name(request.user), 'Platform Governance'),
                'greeting': _greeting(),
                'today_date': timezone.now().strftime('%A, %B %d, %Y'),
            },
            'stats': {
                'total_users': total_users,
                'active_users': active_users,
                'staff_users': staff_users,
                'student_users': student_users,
                'faculties': Faculty.objects.count(),
                'departments': Department.objects.count(),
                'flags_enabled': flags_enabled,
                'flags_total': flags_total,
                'maintenance_active': maintenance_active,
            },
            'role_breakdown': {
                'labels': role_labels,
                'values': role_values,
            },
            'user_growth': {
                'labels': month_labels,
                'new_users': user_series,
                'cumulative': cumulative_users,
            },
            'recent_activities': activities,
            'shortcuts': [
                {'path': '/users', 'title': 'User management', 'description': 'Roles and account access', 'icon': 'fas fa-users'},
                {'path': '/categories', 'title': 'Categories', 'description': 'Faculties and departments', 'icon': 'fas fa-layer-group'},
                {'path': '/operations', 'title': 'Operations', 'description': 'Health and infrastructure', 'icon': 'fas fa-server'},
                {'path': '/settings', 'title': 'Settings', 'description': 'Theme and feature flags', 'icon': 'fas fa-sliders-h'},
                {'path': '/audit', 'title': 'Audit trail', 'description': 'Security and admin events', 'icon': 'fas fa-clipboard-list'},
            ],
        })
