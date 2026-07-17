from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_sub_ec_dual_approval'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ecmembership',
            name='title',
        ),
    ]
