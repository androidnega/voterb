from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_remove_user_level_and_year_of_study'),
        ('elections', '0006_election_register'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Level',
        ),
    ]
