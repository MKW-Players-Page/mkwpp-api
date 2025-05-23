# Generated by Django 5.1.1 on 2024-11-01 19:27

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('timetrials', '0011_playeraward'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteChampion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_instated', models.DateTimeField(default=django.utils.timezone.now)),
                ('category', models.IntegerField(choices=[(0, 'Non-Shortcut'), (1, 'Shortcut'), (2, 'Unrestricted')], default=0)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='timetrials.player')),
            ],
        ),
    ]
