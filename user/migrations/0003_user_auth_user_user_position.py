# Generated by Django 4.2.3 on 2023-08-18 08:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("user", "0002_user_created_at_user_updated_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="auth_user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="users",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="position",
            field=models.CharField(max_length=150, null=True),
        ),
    ]
