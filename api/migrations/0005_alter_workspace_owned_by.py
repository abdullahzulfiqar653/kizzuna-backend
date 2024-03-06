# Generated by Django 4.2.3 on 2024-01-15 14:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_workspace_owned_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workspace',
            name='owned_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='owned_workspaces', to=settings.AUTH_USER_MODEL),
        ),
    ]