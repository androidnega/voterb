from django.db import migrations
from django.db.models import Q


ACADEMIC_STRUCTURE = (
    ('Faculty of Applied Arts and Technology', 'FAAT', 'Ceramics Technology', 'CER'),
    ('Faculty of Applied Arts and Technology', 'FAAT', 'Fashion Design and Technology', 'FDT'),
    ('Faculty of Applied Arts and Technology', 'FAAT', 'Graphic Design Technology', 'GRD'),
    ('Faculty of Applied Arts and Technology', 'FAAT', 'Industrial Painting and Design', 'IPD'),
    ('Faculty of Applied Arts and Technology', 'FAAT', 'Sculpture Technology', 'SCU'),
    ('Faculty of Applied Arts and Technology', 'FAAT', 'Textiles Design and Technology', 'TXT'),
    ('Faculty of Applied Sciences', 'FAS', 'Hospitality Management', 'HOS'),
    ('Faculty of Applied Sciences', 'FAS', 'Industrial and Health Science', 'IHS'),
    ('Faculty of Applied Sciences', 'FAS', 'Computer Science', 'CSC'),
    (
        'Faculty of Applied Sciences',
        'FAS',
        'Mathematics, Statistics and Actuarial Science',
        'MSA',
    ),
    ('Faculty of Applied Sciences', 'FAS', 'Tourism Management', 'TRM'),
    ('Faculty of Built and Natural Environment', 'FBNE', 'Building Technologies', 'BLD'),
    ('Faculty of Built and Natural Environment', 'FBNE', 'Construction Technology', 'CST'),
    ('Faculty of Built and Natural Environment', 'FBNE', 'Estate Management', 'EST'),
    ('Faculty of Built and Natural Environment', 'FBNE', 'Interior Design', 'INT'),
    ('Faculty of Built and Natural Environment', 'FBNE', 'Real Estate', 'REL'),
    ('Faculty of Built and Natural Environment', 'FBNE', 'Plumbing and Gas', 'PLG'),
    ('Faculty of Business Studies', 'FOBS', 'Accounting and Finance', 'ACF'),
    ('Faculty of Business Studies', 'FOBS', 'Marketing and Strategy', 'MKT'),
    ('Faculty of Business Studies', 'FOBS', 'Logistics Management', 'LGM'),
    (
        'Faculty of Business Studies',
        'FOBS',
        'Procurement and Supply Chain Management',
        'PSM',
    ),
    ('Faculty of Business Studies', 'FOBS', 'Transport Management', 'TRN'),
    ('Faculty of Business Studies', 'FOBS', 'Office Management / Secretaryship', 'OFT'),
    ('Faculty of Engineering', 'FENG', 'Civil Engineering', 'CIV'),
    ('Faculty of Engineering', 'FENG', 'Electrical and Electronic Engineering', 'EEE'),
    ('Faculty of Engineering', 'FENG', 'Mechanical Engineering', 'MEC'),
    ('Faculty of Engineering', 'FENG', 'Petroleum and Gas Engineering', 'PEG'),
    ('Faculty of Engineering', 'FENG', 'Renewable Energy Engineering', 'REN'),
    ('Faculty of Engineering', 'FENG', 'Process Engineering', 'PRC'),
    ('Faculty of Engineering', 'FENG', 'Welding and Fabrication', 'WLD'),
    ('Faculty of Health and Allied Sciences', 'FHAS', 'Health Sciences', 'HSC'),
    (
        'Faculty of Health and Allied Sciences',
        'FHAS',
        'Laboratory Technology / Medical Technology',
        'LAB',
    ),
    ('Faculty of Health and Allied Sciences', 'FHAS', 'Pharmacy', 'PHR'),
    (
        'Faculty of Health and Allied Sciences',
        'FHAS',
        'Chemical Pathology / Histopathology / Immunology',
        'CPI',
    ),
    ('Faculty of Maritime and Nautical Studies', 'FMNS', 'Marine Engineering', 'MEN'),
    ('Faculty of Maritime and Nautical Studies', 'FMNS', 'Marine Transport', 'MTR'),
    ('Faculty of Maritime and Nautical Studies', 'FMNS', 'Nautical Science', 'NAU'),
    (
        'Faculty of Media Technology and Liberal Studies',
        'FMTLS',
        'Media and Communication Technology',
        'MCT',
    ),
    (
        'Faculty of Media Technology and Liberal Studies',
        'FMTLS',
        'Liberal Studies / General Arts',
        'LBS',
    ),
)


def seed_categories(apps, schema_editor):
    Faculty = apps.get_model('elections', 'Faculty')
    Department = apps.get_model('elections', 'Department')
    InstitutionCategory = apps.get_model('elections', 'InstitutionCategory')
    InstitutionProfile = apps.get_model('system', 'InstitutionProfile')

    faculties = {}
    for faculty_name, faculty_code, department_name, department_code in ACADEMIC_STRUCTURE:
        faculty = Faculty.objects.filter(code__iexact=faculty_code).first()
        if faculty is None:
            faculty = Faculty.objects.filter(name__iexact=faculty_name).first()
        if faculty is None:
            faculty = Faculty.objects.create(
                name=faculty_name,
                code=faculty_code,
                is_active=True,
            )
        else:
            changed = []
            if faculty.name != faculty_name:
                faculty.name = faculty_name
                changed.append('name')
            if faculty.code != faculty_code:
                faculty.code = faculty_code
                changed.append('code')
            if not faculty.is_active:
                faculty.is_active = True
                changed.append('is_active')
            if changed:
                faculty.save(update_fields=changed)
        faculties[faculty_code] = faculty

        department = Department.objects.filter(code__iexact=department_code).first()
        if department is None:
            department = Department.objects.filter(name__iexact=department_name).first()
        if department is None:
            Department.objects.create(
                name=department_name,
                code=department_code,
                faculty=faculty,
                is_active=True,
            )
        else:
            changed = []
            if department.name != department_name:
                department.name = department_name
                changed.append('name')
            if department.code != department_code:
                department.code = department_code
                changed.append('code')
            if department.faculty_id != faculty.pk:
                department.faculty = faculty
                changed.append('faculty')
            if not department.is_active:
                department.is_active = True
                changed.append('is_active')
            if changed:
                department.save(update_fields=changed)

    institution = InstitutionProfile.objects.filter(
        Q(code__iexact='TTU') | Q(short_name__iexact='TTU')
    ).first()
    if institution:
        category = InstitutionCategory.objects.filter(
            institution=institution,
            name__iexact='Institution',
        ).first()
        if category is None:
            InstitutionCategory.objects.create(
                institution=institution,
                name='Institution',
                code='INST',
                description='Institution-wide category',
                is_active=True,
            )
        else:
            changed = []
            if category.code != 'INST':
                category.code = 'INST'
                changed.append('code')
            if not category.is_active:
                category.is_active = True
                changed.append('is_active')
            if changed:
                category.save(update_fields=changed)


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0014_institutioncategory'),
        ('system', '0003_institution_ec_hierarchy'),
    ]

    operations = [
        migrations.RunPython(seed_categories, migrations.RunPython.noop),
    ]
