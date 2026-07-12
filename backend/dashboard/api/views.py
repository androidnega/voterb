from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import MFALog, User
from accounts.permissions import IsAdminOrSuperAdmin, IsAuditor, IsSuperAdmin
from candidates.models import Candidate
from elections.models import Election, VoterEligibility
from voting.models import Vote


ROLE_LABELS = {
    'admin': 'Election Committee',
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
    permission_classes = [IsAuditor]

    def get(self, request):
        total_elections = Election.objects.count()
        active_elections = Election.objects.filter(status='open').count()
        scheduled_elections = Election.objects.filter(status='scheduled').count()
        closed_elections = Election.objects.filter(status__in=['closed', 'archived']).count()
        total_voters = User.objects.filter(role__name='student').count()
        total_votes = Vote.objects.count()
        unique_voters = Vote.objects.values('user').distinct().count()
        total_candidates = Candidate.objects.filter(status='approved').count()
        eligible_voters = VoterEligibility.objects.filter(is_eligible=True).count()

        turnout_pct = 0
        if eligible_voters > 0:
            turnout_pct = round((unique_voters / eligible_voters) * 100, 1)

        cutoff = timezone.now() - timedelta(days=7)
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        votes_today = Vote.objects.filter(timestamp__gte=today_start).count()
        mfa_logs = MFALog.objects.filter(created_at__gte=cutoff).order_by('-created_at')[:12]
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
            count = Vote.objects.filter(timestamp__gte=start, timestamp__lt=end).count()
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
            count = Election.objects.filter(status=status).count()
            if count > 0:
                status_labels.append(label)
                status_values.append(count)

        live_elections = []
        for election in Election.objects.filter(status__in=['open', 'scheduled', 'paused']).order_by('-start_date')[:6]:
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
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        month_labels = []
        vote_series = []
        user_series = []
        cumulative_users = []

        vote_rows = (
            Vote.objects.annotate(month=TruncMonth('timestamp'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        user_rows = (
            User.objects.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        vote_map = {row['month'].strftime('%b'): row['count'] for row in vote_rows if row['month']}
        user_map = {row['month'].strftime('%b'): row['count'] for row in user_rows if row['month']}

        anchor = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        months = []
        cursor = anchor
        for _ in range(7):
            months.insert(0, cursor)
            cursor = (cursor - timedelta(days=1)).replace(day=1)

        for month_start in months:
            label = month_start.strftime('%b')
            month_labels.append(label)
            vote_series.append(vote_map.get(label, 0))
            user_series.append(user_map.get(label, 0))
            month_end = (month_start + timedelta(days=32)).replace(day=1)
            cumulative_users.append(User.objects.filter(created_at__lt=month_end).count())

        election_status_labels = []
        election_status_values = []
        for status, label in [
            ('open', 'Active'),
            ('scheduled', 'Scheduled'),
            ('closed', 'Closed'),
            ('draft', 'Draft'),
            ('archived', 'Archived'),
        ]:
            count = Election.objects.filter(status=status).count()
            if count > 0:
                election_status_labels.append(label)
                election_status_values.append(count)

        return Response({
            'platform_activity': {
                'labels': month_labels,
                'datasets': [
                    {'label': 'Votes', 'data': vote_series},
                    {'label': 'New users', 'data': user_series},
                ],
            },
            'user_growth': {
                'labels': month_labels,
                'data': cumulative_users,
            },
            'election_stats': {
                'labels': election_status_labels,
                'data': election_status_values,
            },
        })
