# Generated by Django 4.2.3 on 2024-01-17 12:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_note_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='summary',
            field=models.TextField(blank=True),
        ),
    ]