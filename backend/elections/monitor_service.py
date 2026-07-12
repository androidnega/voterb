from datetime import timedelta

from django.utils import timezone

from candidates.models import Candidate
from elections.models import Election, Position
from voting.models import Vote


def get_election_monitor_data(election):
    """Aggregate live monitor data for an election."""
    positions = Position.objects.filter(
        election=election, is_active=True, is_votable=True
    ).order_by('display_order')

    eligible_voters = election.eligibilities.filter(is_eligible=True).count()
    unique_voters = Vote.objects.filter(election=election).values('user').distinct().count()
    total_votes = Vote.objects.filter(election=election).count()

    turnout = 0
    if eligible_voters > 0:
        turnout = round((unique_voters / eligible_voters) * 100, 1)

    now = timezone.now()
    hourly_labels = []
    hourly_buckets = []
    for i in range(11, -1, -1):
        hour_start = (now - timedelta(hours=i)).replace(minute=0, second=0, microsecond=0)
        hour_end = hour_start + timedelta(hours=1)
        hourly_labels.append(hour_start.strftime('%b %d %H:%M'))
        hourly_buckets.append((hour_start, hour_end))

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
                'department': candidate.department,
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

        positions_data.append({
            'uuid': str(pos.uuid),
            'title': pos.title,
            'total_votes': position_vote_total,
            'leader': position_leader,
            'candidates': candidates_data,
            'hourly_trend': {
                'labels': hourly_labels,
                'datasets': pos_hourly_datasets,
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
