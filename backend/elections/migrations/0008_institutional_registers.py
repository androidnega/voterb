import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def backfill_register_institutions(apps, schema_editor):
    VoterRegister = apps.get_model('elections', 'VoterRegister')
    used = set()
    for register in VoterRegister.objects.select_related('election', 'election__created_by').order_by('created_at'):
        if register.institution_id:
            used.add((register.institution_id, register.name.lower()))
            continue
        institution_id = None
        election = register.election
        if election is not None:
            created_by = getattr(election, 'created_by', None)
            if created_by is not None and getattr(created_by, 'institution_id', None):
                institution_id = created_by.institution_id
        if not institution_id:
            continue
        base_name = register.name
        name = base_name
        suffix = 2
        while (institution_id, name.lower()) in used:
            name = f'{base_name} ({suffix})'
            suffix += 1
        register.institution_id = institution_id
        if name != base_name:
            register.name = name
            register.save(update_fields=['institution_id', 'name'])
        else:
            register.save(update_fields=['institution_id'])
        used.add((institution_id, name.lower()))


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0003_institution_ec_hierarchy'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('elections', '0007_delete_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='voterregister',
            name='institution',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='voter_registers',
                to='system.institutionprofile',
            ),
        ),
        migrations.AddField(
            model_name='voterregister',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='registers_created',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='voterregister',
            name='election',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='registers',
                to='elections.election',
            ),
        ),
        migrations.AddField(
            model_name='votercategory',
            name='faculty',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='register_categories',
                to='elections.faculty',
            ),
        ),
        migrations.AddField(
            model_name='votercategory',
            name='department',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='register_categories',
                to='elections.department',
            ),
        ),
        migrations.AddConstraint(
            model_name='votercategory',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(faculty__isnull=True) | models.Q(department__isnull=True)
                ),
                name='voter_category_not_both_faculty_and_department',
            ),
        ),
        migrations.AlterUniqueTogether(
            name='voterregister',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='voterregister',
            constraint=models.UniqueConstraint(
                condition=models.Q(institution__isnull=False),
                fields=('institution', 'name'),
                name='uniq_voterregister_institution_name',
            ),
        ),
        migrations.AddConstraint(
            model_name='voterregister',
            constraint=models.UniqueConstraint(
                condition=models.Q(election__isnull=False),
                fields=('election', 'name'),
                name='uniq_voterregister_election_name',
            ),
        ),
        migrations.RunPython(backfill_register_institutions, migrations.RunPython.noop),
    ]
