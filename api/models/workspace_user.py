from django.db import models

from api.models.user import User


class WorkspaceUser(models.Model):
    class Role(models.TextChoices):
        OWNER = "Owner"
        EDITOR = "Editor"
        VIEWER = "Viewer"

    workspace = models.ForeignKey(
        "Workspace", on_delete=models.CASCADE, related_name="workspace_users"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="workspace_users"
    )
    role = models.CharField(max_length=6, choices=Role.choices, default=Role.VIEWER)

    class Meta:
        unique_together = ("workspace", "user")
