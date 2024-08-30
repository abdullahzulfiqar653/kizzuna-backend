# Generated by Django 4.2.3 on 2024-08-30 07:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import shortuuid.django_fields
from api.models.task_type import default_task_types


def add_default_task_types_for_each_project(apps, schema_editor):
    Project = apps.get_model("api", "Project")
    TaskType = apps.get_model("api", "TaskType")

    task_types_to_create = []
    for project in Project.objects.all():
        existing_task_types = {
            task_type.name: task_type for task_type in project.task_types.all()
        }
        existing_task_type_names = set(existing_task_types.keys())
        for task_type in default_task_types:
            if task_type["name"] not in existing_task_type_names:
                task_types_to_create.append(
                    TaskType(
                        project=project,
                        name=task_type["name"],
                        definition=task_type["definition"],
                    )
                )

    TaskType.objects.bulk_create(task_types_to_create)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0056_contact_googlecalendarattendee_googlecalendarchannel_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="note",
            name="is_approved",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="TaskType",
            fields=[
                (
                    "id",
                    shortuuid.django_fields.ShortUUIDField(
                        alphabet=None,
                        editable=False,
                        length=12,
                        max_length=12,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("definition", models.CharField(max_length=255, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="task_types",
                        to="api.project",
                    ),
                ),
            ],
            options={
                "unique_together": {("project", "name")},
            },
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "id",
                    shortuuid.django_fields.ShortUUIDField(
                        alphabet=None,
                        editable=False,
                        length=12,
                        max_length=12,
                        prefix="",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("due_date", models.DateTimeField(null=True)),
                (
                    "priority",
                    models.CharField(
                        choices=[("Low", "Low"), ("Med", "Med"), ("High", "High")],
                        max_length=4,
                        null=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Todo", "Todo"),
                            ("Done", "Done"),
                            ("Overdue", "Overdue"),
                        ],
                        default="Todo",
                        max_length=8,
                    ),
                ),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assigned_tasks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_tasks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "note",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tasks",
                        to="api.note",
                    ),
                ),
                (
                    "type",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tasks",
                        to="api.tasktype",
                    ),
                ),
            ],
        ),
        migrations.RunPython(
            code=add_default_task_types_for_each_project,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
