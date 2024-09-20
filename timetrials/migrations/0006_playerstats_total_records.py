import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('timetrials', '0005_ranked_regions'),
    ]

    operations = [
        migrations.AddField(
           model_name='playerstats',
           name='total_records',
           field=models.IntegerField(default=0, help_text='Sum of track records'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='playerstats',
            name='leaderboard_points',
            field=models.IntegerField(default=0, help_text='Sum of leaderboard points'),
            preserve_default=False,
        )
    ]