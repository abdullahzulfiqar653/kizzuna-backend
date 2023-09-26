# Generated by Django 4.2.3 on 2023-07-25 04:00

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="User",
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
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("birthday", models.DateField(blank=True, null=True)),
                (
                    "role",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("admin", "ADMIN"),
                            ("manager", "MANAGER"),
                            ("employee", "EMPLOYEE"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                ("last_active_at", models.DateTimeField(blank=True, null=True)),
            ],
        ),
    ]
