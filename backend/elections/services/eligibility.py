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
