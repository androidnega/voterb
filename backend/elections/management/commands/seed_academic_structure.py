import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from elections.models import Faculty, Department

DATA_DIR = Path(__file__).resolve().parents[3] / 'data'
CSV_PATH = DATA_DIR / 'academic_structure.csv'


class Command(BaseCommand):
    help = 'Seed academic structure (Faculties, Departments) from data/academic_structure.csv'

    def handle(self, *args, **options):
        if not CSV_PATH.exists():
            self.stderr.write(self.style.ERROR(f'Missing {CSV_PATH}'))
            return

        faculties_created = 0
        departments_created = 0
        departments_updated = 0

        csv_codes = set()
        csv_faculty_codes = set()

        with open(CSV_PATH, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                faculty_name = row['faculty_name'].strip()
                faculty_code = row['faculty_code'].strip().upper()
                department_name = row['department_name'].strip()
                department_code = row['department_code'].strip().upper()
                csv_codes.add(department_code)
                csv_faculty_codes.add(faculty_code)

                faculty = Faculty.objects.filter(code=faculty_code).first()
                if not faculty:
                    faculty = Faculty.objects.filter(name=faculty_name).first()

                if faculty:
                    faculty.code = faculty_code
                    faculty.name = faculty_name
                    faculty.is_active = True
                    faculty.save()
                else:
                    faculty = Faculty.objects.create(
                        name=faculty_name,
                        code=faculty_code,
                        is_active=True,
                    )
                    faculties_created += 1

                dept = Department.objects.filter(code=department_code).first()
                if not dept:
                    dept = Department.objects.filter(name=department_name).first()

                if dept:
                    dept.code = department_code
                    dept.name = department_name
                    dept.faculty = faculty
                    dept.is_active = True
                    dept.save()
                    departments_updated += 1
                else:
                    Department.objects.create(
                        name=department_name,
                        code=department_code,
                        faculty=faculty,
                        is_active=True,
                    )
                    departments_created += 1

        stale_departments = Department.objects.exclude(code__in=csv_codes).update(is_active=False)
        stale_faculties = Faculty.objects.exclude(code__in=csv_faculty_codes).update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f'Faculties: {Faculty.objects.filter(is_active=True).count()} active | '
            f'Departments: {Department.objects.filter(is_active=True).count()} active '
            f'({departments_created} new, {departments_updated} updated, {stale_departments} deactivated)'
        ))
        if stale_faculties:
            self.stdout.write(self.style.WARNING(f'Deactivated {stale_faculties} legacy faculties'))
