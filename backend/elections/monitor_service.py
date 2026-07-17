from datetime import timedelta
from math import ceil

from django.utils import timezone

from candidates.models import Candidate
from elections.models import Election, Position
from elections.services.register_service import election_register_user_count
from voting.models import Vote


def _monitor_time_buckets(election, now, max_buckets=12):
    """
    Build consecutive time buckets for votes-per-hour charts.

    Prefer recent hourly buckets when votes fall in the last 12 hours;
    otherwise span from the first vote (or election start) so older ballots
    still appear on the monitor instead of an empty chart.
    """
    recent_start = (now - timedelta(hours=11)).replace(minute=0, second=0, microsecond=0)
    has_recent_votes = Vote.objects.filter(
        election=election, timestamp__gte=recent_start
    ).exists()

    if has_recent_votes or not Vote.objects.filter(election=election).exists():
        labels = []
        buckets = []
        for i in range(11, -1, -1):
            hour_start = (now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            labels.append(hour_start.strftime('%b %d %H:%M'))
            buckets.append((hour_start, hour_end))
        return labels, buckets

    first_ts = (
        Vote.objects.filter(election=election)
        .order_by('timestamp')
        .values_list('timestamp', flat=True)
        .first()
    )
    start = first_ts or election.start_date or recent_start
    if timezone.is_naive(start):
        start = timezone.make_aware(start, timezone.get_current_timezone())
    start = start.replace(minute=0, second=0, microsecond=0)
    end = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    if start >= end:
        start = end - timedelta(hours=12)

    span_hours = max(1, int((end - start).total_seconds() // 3600))
    bucket_hours = 1 if span_hours <= max_buckets else max(1, ceil(span_hours / max_buckets))
    bucket_count = min(max_buckets, ceil(span_hours / bucket_hours))
    cursor = end - timedelta(hours=bucket_hours * bucket_count)

    labels = []
    buckets = []
    for i in range(bucket_count):
        hour_start = cursor + timedelta(hours=i * bucket_hours)
        hour_end = hour_start + timedelta(hours=bucket_hours)
        labels.append(hour_start.strftime('%b %d %H:%M'))
        buckets.append((hour_start, hour_end))
    return labels, buckets


def get_election_monitor_data(election):
    """Aggregate live monitor data for an election."""
    positions = Position.objects.filter(
        election=election, is_active=True, is_votable=True
    ).order_by('display_order')

    eligible_voters = election_register_user_count(election)
    unique_voters = Vote.objects.filter(election=election).values('user').distinct().count()
    total_votes = Vote.objects.filter(election=election).count()

    turnout = 0
    if eligible_voters > 0:
        turnout = round((unique_voters / eligible_voters) * 100, 1)

    now = timezone.now()
    hourly_labels, hourly_buckets = _monitor_time_buckets(election, now)

    votes_per_hour = []
    ballots_per_hour = []
    cumulative_turnout_series = []
    for hour_start, hour_end in hourly_buckets:
        votes_per_hour.append(
            Vote.objects.filter(
                election=election,
                timestamp__gte=hour_start,
                timestamp__lt=hour_end,
            ).count()
        )
        ballots_per_hour.append(
            Vote.objects.filter(
                election=election,
                timestamp__gte=hour_start,
                timestamp__lt=hour_end,
            ).values('user').distinct().count()
        )
        voters_so_far = Vote.objects.filter(
            election=election, timestamp__lt=hour_end
        ).values('user').distinct().count()
        pct = round((voters_so_far / eligible_voters) * 100, 1) if eligible_voters else 0
        cumulative_turnout_series.append(pct)

    vote_throughput = {
        'labels': hourly_labels,
        'votes_cast': votes_per_hour,
        'ballots_submitted': ballots_per_hour,
    }
    cumulative_turnout = {
        'labels': hourly_labels,
        'turnout': cumulative_turnout_series,
    }

    positions_data = []
    for pos in positions:
        candidates = Candidate.objects.filter(position=pos, status='approved').order_by('ballot_number')
        candidates_data = []
        position_vote_total = 0

        for candidate in candidates:
            vote_count = Vote.objects.filter(
                election=election, position=pos, candidate=candidate
            ).count()
            position_vote_total += vote_count
            candidates_data.append({
                'uuid': str(candidate.uuid),
                'full_name': candidate.full_name,
                'ballot_number': candidate.ballot_number,
                'photo_url': candidate.photo.url if candidate.photo else None,
                'votes': vote_count,
                'percentage': 0,
            })

        for cand in candidates_data:
            if position_vote_total > 0:
                cand['percentage'] = round((cand['votes'] / position_vote_total) * 100, 1)

        candidates_data.sort(key=lambda x: x['votes'], reverse=True)

        top_candidate = candidates_data[0] if candidates_data and candidates_data[0]['votes'] > 0 else None
        position_leader = None
        if top_candidate:
            position_leader = {
                'uuid': top_candidate['uuid'],
                'full_name': top_candidate['full_name'],
                'percentage': top_candidate['percentage'],
                'votes': top_candidate['votes'],
                'photo_url': top_candidate['photo_url'],
            }

        pos_hourly_datasets = []
        for cand in candidates_data[:4]:
            series = []
            for hour_start, hour_end in hourly_buckets:
                count = Vote.objects.filter(
                    election=election,
                    position=pos,
                    candidate_id=cand['uuid'],
                    timestamp__gte=hour_start,
                    timestamp__lt=hour_end,
                ).count()
                series.append(count)
            pos_hourly_datasets.append({
                'candidate_uuid': cand['uuid'],
                'full_name': cand['full_name'],
                'data': series,
            })

        # Aggregate votes for this race across the same hour buckets
        pos_votes_per_hour = []
        for hour_start, hour_end in hourly_buckets:
            pos_votes_per_hour.append(
                Vote.objects.filter(
                    election=election,
                    position=pos,
                    timestamp__gte=hour_start,
                    timestamp__lt=hour_end,
                ).count()
            )

        positions_data.append({
            'uuid': str(pos.uuid),
            'title': pos.title,
            'total_votes': position_vote_total,
            'leader': position_leader,
            'candidates': candidates_data,
            'hourly_trend': {
                'labels': hourly_labels,
                'datasets': pos_hourly_datasets,
                'votes_cast': pos_votes_per_hour,
            },
        })

    featured_position = positions_data[0] if positions_data else None
    featured_trend = (featured_position or {}).get('hourly_trend', {'labels': hourly_labels, 'datasets': []})

    return {
        'election': {
            'uuid': str(election.uuid),
            'title': election.title,
            'status': election.status,
            'start_date': election.start_date,
            'end_date': election.end_date,
        },
        'positions': positions_data,
        'stats': {
            'total_votes': total_votes,
            'unique_voters': unique_voters,
            'eligible_voters': eligible_voters,
            'turnout': turnout,
        },
        'vote_throughput': vote_throughput,
        'cumulative_turnout': cumulative_turnout,
        'hourly_trend': featured_trend,
        'updated_at': now.isoformat(),
    }
