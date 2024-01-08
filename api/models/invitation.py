from django.db import models

from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class Invitation(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_invitations"
    )
    recipient_email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_user = models.ForeignKey(
        User, null=True, on_delete=models.CASCADE, related_name="invitations"
    )
