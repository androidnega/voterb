"""Voter register services — import CSV and sync eligibility."""

import re

from django.db import transaction
from django.utils import timezone

from accounts.models import Role, User
from elections.models import (
    VoterEligibility,
    VoterRegisterEntry,
    VoterRegisterImport,
)
from elections.services.eligibility import normalize_index_input, resolve_or_create_voter


def election_register_entry_queryset(election):
    """
    Return the voter entries that define the election's scope.

    New architecture: Election.register is the primary voter list.
    Transitional fallback: if no primary register is selected yet, use any
    legacy register still owned by the election.
    """
    qs = VoterRegisterEntry.objects.filter(user__isnull=False)
    if getattr(election, 'register_id', None):
        return qs.filter(register_id=election.register_id)
    return qs.filter(register__election=election)


def election_register_user_count(election) -> int:
    """Count distinct linked students in the election's register scope."""
    return election_register_entry_queryset(election).values('user_id').distinct().count()


def user_is_on_election_register(user, election) -> bool:
    """True when the user has an entry in the election's register scope."""
    return election_register_entry_queryset(election).filter(user=user).exists()


def parse_full_name(full_name: str):
    parts = (full_name or '').strip().split(None, 1)
    if not parts:
        return 'Student', ''
    if len(parts) == 1:
        return parts[0], ''
    return parts[0], parts[1]


def normalize_gender(value: str) -> str:
    raw = (value or '').strip()
    if not raw:
        return ''
    mapping = {
        'm': 'Male',
        'male': 'Male',
        'f': 'Female',
        'female': 'Female',
        'other': 'Other',
        'o': 'Other',
    }
    return mapping.get(raw.lower(), raw if raw in ('Male', 'Female', 'Other') else '')


@transaction.atomic
def sync_eligibility_from_registers(election, verified_by=None):
    """
    Upsert VoterEligibility for every linked register entry user.
    Keeps legacy eligibility table in sync for dashboards/counts.
    """
    entries = election_register_entry_queryset(election).select_related('user')
    user_ids = set()
    created = 0
    for entry in entries:
        user_ids.add(entry.user_id)
        _, was_created = VoterEligibility.objects.get_or_create(
            election=election,
            user=entry.user,
            defaults={
                'is_eligible': True,
                'eligibility_reason': 'Synced from voter register',
                'verified_by': verified_by,
                'verified_at': timezone.now() if verified_by else None,
            },
        )
        if was_created:
            created += 1
        else:
            VoterEligibility.objects.filter(election=election, user=entry.user).update(
                is_eligible=True,
            )

    # Soft-disable eligibility for users no longer on any register
    if user_ids:
        VoterEligibility.objects.filter(election=election).exclude(user_id__in=user_ids).update(
            is_eligible=False,
            eligibility_reason='Removed from voter register',
        )
    else:
        VoterEligibility.objects.filter(election=election).update(
            is_eligible=False,
            eligibility_reason='No register entries',
        )
    return created


def _normalize_csv_header(value: str) -> str:
    """Collapse headers so Index Number / index_number / INDEX-NUMBER match."""
    return re.sub(r'[^a-z0-9]', '', (value or '').strip().lower())


def _looks_like_index(value: str) -> bool:
    text = (value or '').strip()
    if not text or '@' in text:
        return False
    if '/' in text and re.search(r'[A-Za-z].*\d|\d.*[A-Za-z]', text):
        return True
    if re.match(r'^[A-Za-z]{2}\d{4}[A-Za-z]{2}\d+$', text):
        return True
    if re.match(r'^[A-Za-z]{2}[A-Za-z]{3}\d{2}\d+$', text):
        return True
    return False


def _looks_like_phone(value: str) -> bool:
    text = (value or '').strip()
    if not text:
        return False
    digits = re.sub(r'\D', '', text)
    return 9 <= len(digits) <= 15 and not re.search(r'[A-Za-z]', text)


def _looks_like_name(value: str) -> bool:
    text = (value or '').strip()
    if not text or '@' in text or _looks_like_index(text) or _looks_like_phone(text):
        return False
    letters = re.sub(r'[^A-Za-z]', '', text)
    return len(letters) >= 2 and bool(re.search(r'[A-Za-z]', text))


def resolve_register_csv_columns(fieldnames, sample_rows=None):
    """
    Intelligently map CSV headers to index_number, full_name, phone_number.

    Extra columns are ignored. Uses alias matching first, then header tokens,
    then sample-row value heuristics when headers are unclear.
    """
    INDEX_ALIASES = {
        'indexnumber', 'index', 'indexno', 'indexnum', 'voterid', 'identifier',
        'studentid', 'studentindex', 'studentno', 'studentnumber', 'regno',
        'registrationnumber', 'matricno',
    }
    NAME_ALIASES = {
        'fullname', 'name', 'studentname', 'votername', 'fullnameofstudent',
        'studentfullname', 'surnamefirstname',
    }
    PHONE_ALIASES = {
        'phonenumber', 'phone', 'mobile', 'mobilenumber', 'tel', 'telephone',
        'contact', 'contactnumber', 'cellphone', 'whatsapp', 'msisdn',
    }

    headers = [h for h in (fieldnames or []) if h and str(h).strip()]
    if not headers:
        raise ValueError(
            'CSV has no header row. Download the voter template and use '
            'index_number, full_name, phone_number.'
        )

    normalized = {h: _normalize_csv_header(h) for h in headers}
    samples = sample_rows or []

    def score_header(header: str, field: str) -> float:
        key = normalized[header]
        aliases = {
            'index': INDEX_ALIASES,
            'name': NAME_ALIASES,
            'phone': PHONE_ALIASES,
        }[field]
        score = 0.0
        if key in aliases:
            score += 100.0

        tokens = {
            'index': ('index', 'voterid', 'studentid', 'regno', 'matric'),
            'name': ('fullname', 'name', 'surname', 'firstname'),
            'phone': ('phone', 'mobile', 'tel', 'contact', 'whatsapp', 'msisdn'),
        }[field]
        for token in tokens:
            if token in key:
                score += 25.0
                break

        values = []
        for row in samples[:40]:
            raw = row.get(header)
            text = '' if raw is None else str(raw).strip()
            if text:
                values.append(text)
        if values:
            if field == 'index':
                hits = sum(1 for v in values if _looks_like_index(v))
                score += (hits / len(values)) * 40.0
            elif field == 'phone':
                hits = sum(1 for v in values if _looks_like_phone(v))
                score += (hits / len(values)) * 40.0
            elif field == 'name':
                hits = sum(1 for v in values if _looks_like_name(v))
                score += (hits / len(values)) * 35.0
                multi = sum(1 for v in values if len(v.split()) >= 2)
                score += (multi / len(values)) * 10.0
        return score

    def pick_best(field: str, used: set, min_score: float):
        ranked = []
        for header in headers:
            if header in used:
                continue
            ranked.append((score_header(header, field), header))
        ranked.sort(key=lambda item: item[0], reverse=True)
        if not ranked or ranked[0][0] < min_score:
            return None
        return ranked[0][1]

    used = set()
    index_col = pick_best('index', used, min_score=20.0)
    if index_col:
        used.add(index_col)
    name_col = pick_best('name', used, min_score=15.0)
    if name_col:
        used.add(name_col)
    phone_col = pick_best('phone', used, min_score=15.0)
    if phone_col:
        used.add(phone_col)

    missing = []
    if not index_col:
        missing.append('index number (index_number / index / index number)')
    if not name_col:
        missing.append('full name (full_name / name / full name / fullname)')
    if missing:
        found = ', '.join(h.strip() for h in headers) or 'none'
        raise ValueError(
            'Could not map required CSV columns: '
            + '; '.join(missing)
            + f'. Found headers: {found}. '
            'Download the voter template for the expected format. Extra columns are ignored.'
        )

    return {
        'index': index_col,
        'name': name_col,
        'phone': phone_col,
        'ignored': [h for h in headers if h not in used],
    }


@transaction.atomic
def import_register_csv(*, register, category, file_obj, imported_by):
    """
    Import CSV rows into a register category.

    Uses intelligent column detection for index, full name, and phone.
    Extra columns are ignored. Blank phones are stored as null.
    """
    import csv
    import io

    def normalize_phone(value: str):
        phone = (value or '').strip()
        if not phone:
            return None
        cleaned = re.sub(r'[^\d+]', '', phone)
        return cleaned or None

    raw = file_obj.read()
    if isinstance(raw, bytes):
        decoded = raw.decode('utf-8-sig')
    else:
        decoded = raw

    preview_reader = csv.DictReader(io.StringIO(decoded))
    if not preview_reader.fieldnames:
        raise ValueError(
            'CSV has no header row. Download the voter template and use '
            'index_number, full_name, phone_number.'
        )
    sample_rows = []
    for i, row in enumerate(preview_reader):
        sample_rows.append(row)
        if i >= 39:
            break

    mapping = resolve_register_csv_columns(preview_reader.fieldnames, sample_rows)
    index_key = mapping['index']
    name_key = mapping['name']
    phone_key = mapping['phone']

    reader = csv.DictReader(io.StringIO(decoded))
    rows_processed = 0
    rows_created = 0
    errors = []
    student_role, _ = Role.objects.get_or_create(name='student')

    for row in reader:
        rows_processed += 1
        voter_id_raw = ('' if row.get(index_key) is None else str(row.get(index_key))).strip()
        full_name = ('' if row.get(name_key) is None else str(row.get(name_key))).strip()
        phone_raw = (
            '' if not phone_key or row.get(phone_key) is None else str(row.get(phone_key))
        ).strip()
        phone_number = normalize_phone(phone_raw)

        if not voter_id_raw:
            errors.append(f'Row {rows_processed}: missing index number')
            continue
        if not full_name:
            errors.append(f'Row {rows_processed}: missing full name for {voter_id_raw}')
            continue

        voter_id = normalize_index_input(voter_id_raw)
        if '@' in voter_id:
            errors.append(f'{voter_id}: use index numbers only, not email')
            continue

        user, err = resolve_or_create_voter(voter_id)
        if err or not user:
            if User.objects.filter(index_number=voter_id).exists():
                user = User.objects.get(index_number=voter_id)
            else:
                first_name, last_name = parse_full_name(full_name)
                user = User.objects.create(
                    index_number=voter_id,
                    email=None,
                    first_name=first_name or 'Student',
                    last_name=last_name or voter_id.split('/')[-1],
                    phone_number=phone_number,
                    role=student_role,
                    is_verified=True,
                    is_active=True,
                )
        else:
            first_name, last_name = parse_full_name(full_name)
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name

        update_fields = ['first_name', 'last_name']
        if phone_number is not None:
            user.phone_number = phone_number
            update_fields.append('phone_number')
        if getattr(category, 'department_id', None):
            user.department = category.department
            user.faculty = category.department.faculty
            update_fields.extend(['department', 'faculty'])
        elif getattr(category, 'faculty_id', None):
            user.faculty = category.faculty
            update_fields.append('faculty')
        user.save(update_fields=list(dict.fromkeys(update_fields)))

        existing = VoterRegisterEntry.objects.filter(register=register, voter_id=voter_id).first()
        if existing:
            existing.full_name = full_name
            existing.phone_number = phone_number
            existing.category = category
            existing.user = user
            existing.save(update_fields=['full_name', 'phone_number', 'category', 'user'])
            continue

        VoterRegisterEntry.objects.create(
            register=register,
            category=category,
            voter_id=voter_id,
            full_name=full_name,
            phone_number=phone_number,
            user=user,
        )
        rows_created += 1

    import_record = VoterRegisterImport.objects.create(
        register=register,
        file_name=getattr(file_obj, 'name', 'import.csv')[:255],
        rows_processed=rows_processed,
        rows_created=rows_created,
        errors=errors,
        imported_by=imported_by,
    )
    # Staging replace drafts are applied on dual approval — don't sync yet.
    if getattr(register, 'replace_of_id', None):
        return import_record

    from elections.models import Election
    election_ids = set(
        Election.objects.filter(register=register).values_list('id', flat=True)
    )
    if register.election_id:
        election_ids.add(register.election_id)
    for election in Election.objects.filter(id__in=election_ids):
        sync_eligibility_from_registers(election, verified_by=imported_by)
    return import_record


@transaction.atomic
def apply_register_replace(*, live_register, staging_register, target_category_uuid=None, verified_by=None):
    """
    Apply a dual-approved register re-upload.

    Replaces voters in the target live category (or all categories if omitted)
    with staging entries, then syncs eligibility for every election using the
    live institutional register (Main EC + Sub EC).
    """
    from elections.models import Election, VoterCategory

    if staging_register.replace_of_id != live_register.pk:
        raise ValueError('Staging register does not belong to this live register.')

    # Map staging categories → live categories by faculty/department identity.
    live_cats = list(
        VoterCategory.objects.filter(register=live_register)
        .select_related('faculty', 'department')
    )
    staging_cats = list(
        VoterCategory.objects.filter(register=staging_register)
        .select_related('faculty', 'department')
    )

    def cat_key(cat):
        return (
            str(cat.faculty_id or ''),
            str(cat.department_id or ''),
            (cat.name or '').strip().lower(),
        )

    live_by_key = {cat_key(c): c for c in live_cats}
    pairs = []
    for staging_cat in staging_cats:
        live_cat = live_by_key.get(cat_key(staging_cat))
        if not live_cat:
            # Fallback: first live category with same faculty/dept ignoring name
            live_cat = next(
                (
                    c for c in live_cats
                    if c.faculty_id == staging_cat.faculty_id
                    and c.department_id == staging_cat.department_id
                ),
                None,
            )
        if live_cat:
            pairs.append((live_cat, staging_cat))

    if target_category_uuid:
        pairs = [
            (live_cat, staging_cat)
            for live_cat, staging_cat in pairs
            if str(live_cat.uuid) == str(target_category_uuid)
        ]

    if not pairs:
        raise ValueError('Could not match staging categories to the live register.')

    for live_cat, staging_cat in pairs:
        # Full replace for this category container.
        VoterRegisterEntry.objects.filter(register=live_register, category=live_cat).delete()
        new_entries = []
        for entry in VoterRegisterEntry.objects.filter(register=staging_register, category=staging_cat):
            new_entries.append(VoterRegisterEntry(
                register=live_register,
                category=live_cat,
                voter_id=entry.voter_id,
                full_name=entry.full_name,
                phone_number=entry.phone_number,
                gender=entry.gender,
                user=entry.user,
            ))
        if new_entries:
            VoterRegisterEntry.objects.bulk_create(new_entries)

    # Sync every election that shares this institutional register.
    elections = Election.objects.filter(register=live_register)
    synced = 0
    for election in elections:
        sync_eligibility_from_registers(election, verified_by=verified_by)
        synced += 1

    staging_register.delete()
    return {'categories_replaced': len(pairs), 'elections_synced': synced}
