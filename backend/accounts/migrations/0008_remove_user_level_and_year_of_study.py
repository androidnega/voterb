from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_ecmembership_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='level',
        ),
        migrations.RemoveField(
            model_name='user',
            name='year_of_study',
        ),
    ]
