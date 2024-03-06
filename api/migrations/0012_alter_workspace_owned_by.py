# Generated by Django 4.2.3 on 2024-01-24 11:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_remove_tag_takeaway_count_takeaway_updated_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workspace',
            name='owned_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_workspaces', to=settings.AUTH_USER_MODEL),
        ),
    ]