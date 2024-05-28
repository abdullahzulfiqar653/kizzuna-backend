# Generated by Django 4.2.3 on 2024-05-17 07:01

from django.db import migrations, models


def update_workspace_owner_role(apps, schema_editor):
    WorkspaceUser = apps.get_model("api", "WorkspaceUser")
    Workspace = apps.get_model("api", "Workspace")

    for workspace in Workspace.objects.all():
        workspace_user = WorkspaceUser.objects.get(
            workspace=workspace, user=workspace.owned_by
        )
        workspace_user.role = "Owner"
        workspace_user.save()


def revert_workspace_owner_role(apps, schema_editor):
    WorkspaceUser = apps.get_model("api", "WorkspaceUser")
    WorkspaceUser.objects.filter(role="Owner").update(role="Editor")


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0030_workspaceuser_alter_workspace_members"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workspaceuser",
            name="role",
            field=models.CharField(
                choices=[
                    ("Owner", "Owner"),
                    ("Editor", "Editor"),
                    ("Viewer", "Viewer"),
                ],
                default="Viewer",
                max_length=6,
            ),
        ),
        migrations.RunPython(
            code=update_workspace_owner_role,
            reverse_code=revert_workspace_owner_role,
        ),
    ]
