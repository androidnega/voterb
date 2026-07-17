from django.db import migrations


def fix_moolre_sms_url(apps, schema_editor):
    SystemSetting = apps.get_model('system', 'SystemSetting')
    setting = SystemSetting.objects.filter(key='sms_moolre_url').first()
    if not setting:
        SystemSetting.objects.create(
            key='sms_moolre_url',
            value='https://api.moolre.com/open/sms/send',
            category='integrations',
            description='Moolre SMS API URL',
        )
        return
    current = (setting.value or '').strip()
    if not current or '/v1/sms/send' in current:
        setting.value = 'https://api.moolre.com/open/sms/send'
        setting.save(update_fields=['value'])


class Migration(migrations.Migration):
    dependencies = [
        ('system', '0004_set_session_timeout_minutes'),
    ]

    operations = [
        migrations.RunPython(fix_moolre_sms_url, migrations.RunPython.noop),
    ]
