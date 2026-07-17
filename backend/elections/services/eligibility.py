import re

from accounts.models import Role, User


def normalize_index_input(identifier: str) -> str:
    """Accept slashless indexes (e.g. SC2021PL001) and normalize for storage."""
    identifier = (identifier or '').strip()
    if not identifier or '/' in identifier:
        return identifier

    match = re.match(r'^([A-Za-z]{2})(\d{4})([A-Za-z]{2})(\d+)$', identifier)
    if match:
        return f'{match.group(1).upper()}/{match.group(2)}/{match.group(3).upper()}/{match.group(4)}'

    match = re.match(r'^([A-Za-z]{2})([A-Za-z]{3})(\d{2})(\d+)$', identifier)
    if match:
        return f'{match.group(1).upper()}/{match.group(2).upper()}/{match.group(3)}/{match.group(4)}'

    return identifier


def apply_student_academic_placement(
    user,
    *,
    faculty_uuid=None,
    department_uuid=None,
    faculty_code=None,
    department_code=None,
    clear_missing=False,
):
    """
    Assign faculty / department on a student account (EC/admin).
    Raises ValueError with a user-facing message on bad refs.
    """
    from elections.models import Department, Faculty

    faculty = user.faculty
    department = user.department

    if faculty_uuid is not None or faculty_code is not None:
        if faculty_uuid:
            faculty = Faculty.objects.filter(uuid=faculty_uuid, is_active=True).first()
            if not faculty:
                raise ValueError('Faculty not found.')
        elif faculty_code:
            code = str(faculty_code).strip()
            faculty = Faculty.objects.filter(code__iexact=code, is_active=True).first()
            if not faculty:
                faculty = Faculty.objects.filter(name__iexact=code, is_active=True).first()
            if not faculty:
                raise ValueError(f'Faculty "{code}" not found.')
        elif clear_missing:
            faculty = None

    if department_uuid is not None or department_code is not None:
        if department_uuid:
            department = Department.objects.filter(uuid=department_uuid, is_active=True).first()
            if not department:
                raise ValueError('Department not found.')
        elif department_code:
            code = str(department_code).strip()
            qs = Department.objects.filter(is_active=True)
            if faculty:
                qs = qs.filter(faculty=faculty)
            department = qs.filter(code__iexact=code).first()
            if not department:
                department = qs.filter(name__iexact=code).first()
            if not department:
                raise ValueError(f'Department "{code}" not found.')
        elif clear_missing:
            department = None

    if faculty and department and department.faculty_id != faculty.pk:
        raise ValueError('Department does not belong to the selected faculty.')

    if department and not faculty:
        faculty = department.faculty

    user.faculty = faculty
    user.department = department
    return user


def resolve_or_create_voter(index_number: str):
    """
    Find a student by index number. Auto-create accounts for valid index formats.
    Students have no email — index is the sole identity.
    Returns (user, error_message).
    """
    index_number = normalize_index_input(index_number)
    if not index_number:
        return None, 'Enter a student index number (e.g. SC/2021/PL/001).'

    if '@' in index_number:
        return (
            None,
            'Students are identified by index number only. '
            'Enter the full index, e.g. SC/2021/PL/001.',
        )

    user = User.objects.filter(index_number=index_number).first()
    if user:
        return user, None

    if '/' not in index_number:
        return (
            None,
            f'No student found with index "{index_number}". '
            'Use the full index format, e.g. SC/2021/PL/001.',
        )

    student_role, _ = Role.objects.get_or_create(name='student')
    user = User.objects.create(
        index_number=index_number,
        email=None,
        first_name='Student',
        last_name=index_number.split('/')[-1],
        role=student_role,
        is_verified=True,
        is_active=True,
    )
    return user, None
