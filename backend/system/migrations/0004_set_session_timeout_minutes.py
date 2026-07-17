from django.db import migrations


def set_session_timeout_minutes(apps, schema_editor):
    SystemSetting = apps.get_model('system', 'SystemSetting')
    setting, created = SystemSetting.objects.get_or_create(
        key='session_timeout_minutes',
        defaults={
            'category': 'security',
            'value': '20',
            'description': 'Session timeout in minutes',
        },
    )
    if created:
        return
    current = (setting.value or '').strip()
    if not current or current == '30':
        setting.value = '20'
        setting.save(update_fields=['value'])


class Migration(migrations.Migration):
    dependencies = [
        ('system', '0003_institution_ec_hierarchy'),
    ]

    operations = [
        migrations.RunPython(set_session_timeout_minutes, migrations.RunPython.noop),
    ]
