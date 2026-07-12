"""Resolve and apply current academic structure references."""

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
    candidate.academic_department = department
    candidate.faculty = department.faculty
    candidate.department = department.name
    candidate.save(update_fields=['academic_department', 'faculty', 'department', 'updated_at'])


def sync_candidate_department(candidate, *, department_code: str | None = None) -> bool:
    """Resolve and persist academic refs on a candidate. Returns True if updated."""
    department = resolve_department(
        code=department_code,
        name=candidate.department if not department_code else None,
    )
    if not department:
        return False
    apply_department_to_candidate(candidate, department)
    return True
