from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import MFALog, User
from elections.models import Election, VoterEligibility
from voting.models import Vote
from accounts.permissions import IsAdminOrSuperAdmin

class AdminDashboardView(APIView):
    permission_classes = [IsAdminOrSuperAdmin]

    def get(self, request):
        # Stats
        total_elections = Election.objects.count()
        active_elections = Election.objects.filter(status='open').count()
        total_voters = User.objects.filter(role__name='student').count()
        total_votes = Vote.objects.count()
        eligible_voters = VoterEligibility.objects.filter(is_eligible=True).count()
        turnout_pct = 0
        if eligible_voters > 0:
            turnout_pct = round((total_votes / eligible_voters) * 100, 2)

        # Recent Activities (last 7 days)
        cutoff = timezone.now() - timedelta(days=7)
        mfa_logs = MFALog.objects.filter(created_at__gte=cutoff).order_by('-created_at')[:10]
        activities = []
        for log in mfa_logs:
            actor = (log.user.email if log.user and log.user.email else None) or (
                log.user.index_number if log.user else 'Unknown'
            )
            activities.append({
                'type': 'login' if 'login' in log.event_type else 'vote' if 'vote' in log.event_type else 'other',
                'icon': self._get_icon(log.event_type),
                'message': f"{actor} - {log.event_type}",
                'time': log.created_at.strftime('%b %d, %I:%M %p')
            })

        # Chart data (last 7 days, daily vote counts)
        chart_dates = []
        chart_counts = []
        for i in range(6, -1, -1):
            day = timezone.now() - timedelta(days=i)
            start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
            count = Vote.objects.filter(timestamp__gte=start, timestamp__lt=end).count()
            chart_dates.append(day.strftime('%b %d'))
            chart_counts.append(count)

        return Response({
            'stats': {
                'total_elections': total_elections,
                'active_elections': active_elections,
                'total_voters': total_voters,
                'turnout': turnout_pct
            },
            'recent_activities': activities,
            'chart_data': {
                'labels': chart_dates,
                'values': chart_counts
            }
        })

    def _get_icon(self, event_type):
        if 'login' in event_type:
            return 'pi pi-sign-in'
        elif 'vote' in event_type:
            return 'pi pi-check-circle'
        elif 'otp' in event_type:
            return 'pi pi-shield'
        elif 'election' in event_type:
            return 'pi pi-calendar'
        else:
            return 'pi pi-info-circle'
