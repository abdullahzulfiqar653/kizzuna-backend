# Generated by Django 4.2.3 on 2024-01-17 00:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_workspace_owned_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='url',
            field=models.URLField(max_length=255, null=True),
        ),
    ]
