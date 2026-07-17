from django.db import migrations, models
from django.db.models import Q


def backfill_audience(apps, schema_editor):
    VoterRegister = apps.get_model('elections', 'VoterRegister')
    VoterCategory = apps.get_model('elections', 'VoterCategory')
    for register in VoterRegister.objects.all().iterator():
        has_sub_scope = VoterCategory.objects.filter(register=register).filter(
            Q(faculty_id__isnull=False) | Q(department_id__isnull=False),
        ).exists()
        register.audience = 'sub' if has_sub_scope else 'main'
        register.save(update_fields=['audience'])


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0012_register_replace_staging'),
    ]

    operations = [
        migrations.AddField(
            model_name='voterregister',
            name='audience',
            field=models.CharField(
                choices=[
                    ('main', 'Main EC (institution-wide)'),
                    ('sub', 'Sub EC (faculty / department)'),
                ],
                db_index=True,
                default='sub',
                max_length=10,
            ),
        ),
        migrations.RunPython(backfill_audience, migrations.RunPython.noop),
    ]
