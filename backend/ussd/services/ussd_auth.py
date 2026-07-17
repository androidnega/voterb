"""USSD auth helpers — MSISDN normalize, index lookup, voted lockout."""

from __future__ import annotations

import re

from django.db.models import Q

from accounts.models import User
from elections.models import Election, VoterEligibility, VoterRegisterEntry
from voting.models import Vote

INDEX_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9\/\-\.]{2,49}$')


def normalize_msisdn(raw: str | None) -> str:
    digits = re.sub(r'\D', '', raw or '')
    if digits.startswith('0') and len(digits) == 10:
        digits = '233' + digits[1:]
    if digits.startswith('2330') and len(digits) == 13:
        digits = '233' + digits[4:]
    return digits


def normalize_index(raw: str | None) -> str:
    return re.sub(r'\s+', '', (raw or '').strip()).upper()


def is_valid_index_format(raw: str) -> bool:
    value = normalize_index(raw)
    return bool(value) and bool(INDEX_PATTERN.fullmatch(value)) and len(value) >= 3


def find_users_by_msisdn(msisdn: str):
    normalized = normalize_msisdn(msisdn)
    if not normalized:
        return User.objects.none()
    local = normalized[3:] if normalized.startswith('233') and len(normalized) > 3 else normalized
    return User.objects.filter(
        Q(phone_number__icontains=normalized)
        | Q(phone_number__icontains=local)
        | Q(phone_number__icontains=f'+{normalized}')
        | Q(phone_number__icontains=f'0{local}')
    )


def msisdn_matches_phone(msisdn: str, phone: str | None) -> bool:
    a = normalize_msisdn(msisdn)
    b = normalize_msisdn(phone or '')
    if not a or not b:
        return False
    return a == b or a.endswith(b[-9:]) or b.endswith(a[-9:])


def open_ussd_elections():
    return Election.objects.filter(status='open', allow_ussd_voting=True)


def user_ballot_complete(user, election: Election) -> bool:
    """True when voter has cast at least one vote and has no remaining open positions."""
    if not Vote.objects.filter(user=user, election=election).exists():
        return False
    from elections.models import Position

    voted_ids = set(
        Vote.objects.filter(user=user, election=election).values_list('position_id', flat=True)
    )
    positions = list(
        Position.objects.filter(
            election=election,
            is_active=True,
            is_votable=True,
        )
        .exclude(pk__in=voted_ids)
        .prefetch_related('restricted_categories')
    )
    remaining = [p for p in positions if p.voter_may_see(user)]
    return len(remaining) == 0


def msisdn_already_voted(msisdn: str) -> bool:
    """
    Contact lockout for *currently open* USSD elections only.

    Do not use historical USSDSession ballot_complete flags — those permanently
    blocked the number after any past vote (including closed elections).
    """
    from elections.services.register_service import election_register_entry_queryset

    open_elections = list(open_ussd_elections())
    if not open_elections:
        return False

    users = list(find_users_by_msisdn(msisdn)[:30])
    if not users:
        return False

    considered = 0
    remaining = 0
    for user in users:
        for election in open_elections:
            eligibility = VoterEligibility.objects.filter(election=election, user=user).first()
            if eligibility is not None and not eligibility.is_eligible:
                continue
            on_register = election_register_entry_queryset(election).filter(user=user).exists()
            if not on_register and eligibility is None:
                continue
            considered += 1
            if not user_ballot_complete(user, election):
                remaining += 1

    if considered == 0:
        return False
    return remaining == 0


def resolve_index_candidates(raw_index: str, msisdn: str | None = None):
    """
    Resolve open USSD elections for an index number.
    Prefers register entries / users whose phone matches the dialing MSISDN.
    Returns list of dicts: {user, election, title, ...}.
    """
    index = normalize_index(raw_index)
    if not index:
        return []

    users = list(
        User.objects.filter(index_number__iexact=index, is_active=True)[:10]
    )
    entry_qs = list(
        VoterRegisterEntry.objects.filter(voter_id__iexact=index)
        .select_related('user')
        .order_by('-created_at')[:30]
    )
    for entry in entry_qs:
        if entry.user_id and entry.user not in users:
            users.append(entry.user)

    if not users:
        return []

    if msisdn:
        phone_matched = []
        for u in users:
            if msisdn_matches_phone(msisdn, u.phone_number):
                phone_matched.append(u)
                continue
            if any(
                e.user_id == u.pk and msisdn_matches_phone(msisdn, e.phone_number)
                for e in entry_qs
            ):
                phone_matched.append(u)
        if phone_matched:
            users = phone_matched

    results = []
    seen = set()
    for user in users:
        for election in open_ussd_elections().order_by('title'):
            from elections.services.register_service import election_register_entry_queryset
            on_register = election_register_entry_queryset(election).filter(
                Q(user=user) | Q(voter_id__iexact=index)
            ).exists()
            eligibility = VoterEligibility.objects.filter(
                election=election, user=user,
            ).first()
            if eligibility is not None and not eligibility.is_eligible:
                continue
            if not on_register and eligibility is None:
                continue

            # Skip ballots already completed for this open election so the
            # voter can still reach another open election they are eligible for.
            if user_ballot_complete(user, election):
                continue

            key = (str(user.uuid), str(election.uuid))
            if key in seen:
                continue
            seen.add(key)
            results.append({
                'user': user,
                'election': election,
                'title': election.title,
                'user_uuid': str(user.uuid),
                'election_uuid': str(election.uuid),
            })
    return results
