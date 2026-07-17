"""Resolve academic structure references (faculties / departments).

Candidate academic fields were removed in Phase 4; department resolution is
retained for voter / eligibility tooling that still maps free-text labels.
"""

from __future__ import annotations

from elections.models import Department

# Legacy free-text labels from early demo seeds → current department codes (academic_structure.csv)
LEGACY_DEPARTMENT_CODES = {
    'computer science': 'CSC',
    'information technology': 'CSC',
    'engineering': 'MEC',
    'electrical engineering': 'EEE',
    'business': 'MKT',
    'management': 'MKT',
    'education': 'LBS',
    'law': 'LBS',
    'english': 'LBS',
    'history': 'LBS',
    'finance': 'ACF',
    'accounting': 'ACF',
    'mathematics': 'MSA',
    'statistics': 'MSA',
    'nursing': 'HSC',
    'public health': 'HSC',
}


def resolve_department(*, code: str | None = None, name: str | None = None) -> Department | None:
    """Return an active department by code, exact name, or legacy alias."""
    qs = Department.objects.filter(is_active=True, faculty__is_active=True).select_related('faculty')

    if code:
        department = qs.filter(code=code.strip().upper()).first()
        if department:
            return department

    if name:
        cleaned = name.strip()
        if not cleaned:
            return None

        department = qs.filter(name__iexact=cleaned).first()
        if department:
            return department

        legacy_code = LEGACY_DEPARTMENT_CODES.get(cleaned.lower())
        if legacy_code:
            return qs.filter(code=legacy_code).first()

    return None


def apply_department_to_candidate(candidate, department: Department) -> None:
    """No-op: candidates no longer store faculty/department fields."""
    return None


def sync_candidate_department(candidate, *, department_code: str | None = None) -> bool:
    """No-op: candidates no longer store faculty/department fields."""
    return False
