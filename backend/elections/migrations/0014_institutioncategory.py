from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0013_voterregister_audience'),
        ('system', '0003_institution_ec_hierarchy'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstitutionCategory',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('code', models.CharField(blank=True, max_length=20)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'institution',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='institution_categories',
                        to='system.institutionprofile',
                    ),
                ),
            ],
            options={
                'verbose_name_plural': 'institution categories',
            },
        ),
        migrations.AddConstraint(
            model_name='institutioncategory',
            constraint=models.UniqueConstraint(
                fields=('institution', 'name'),
                name='uniq_institutioncategory_institution_name',
            ),
        ),
    ]
