# Generated by Django 4.2.3 on 2024-07-23 09:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0050_delete_chunk"),
    ]

    operations = [
        migrations.AddField(
            model_name="note",
            name="google_drive_file_timestamp",
            field=models.DateTimeField(null=True),
        ),
        migrations.CreateModel(
            name="GoogleDriveOAuthState",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("state", models.CharField(max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="GoogleDriveCredential",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("access_token", models.CharField(max_length=255)),
                ("refresh_token", models.CharField(max_length=255)),
                (
                    "token_type",
                    models.CharField(
                        choices=[
                            ("Access", "Access"),
                            ("Refresh", "Refresh"),
                            ("Bearer", "Bearer"),
                        ],
                        max_length=50,
                    ),
                ),
                ("expires_in", models.IntegerField()),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="google_drive_credentials",
                        to="api.project",
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
