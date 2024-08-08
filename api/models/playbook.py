from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.takeaway import Takeaway
from api.models.user import User
from api.models.note import Note
from api.models.workspace import Workspace
from api.models.project import Project


class PlayBook(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="playbooks"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="playbooks"
    )
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="playbooks"
    )
    clip = models.FileField(
        upload_to="attachments/",
        null=True,
        max_length=255,
    )
    thumbnail = models.ImageField(upload_to="thumbnails/", null=True)
    clip_size = models.PositiveIntegerField(
        null=True, help_text="File size measured in bytes."
    )
    thumbnail_size = models.PositiveIntegerField(
        null=True, help_text="Image size measured in bytes."
    )
    notes = models.ManyToManyField(Note, related_name="playbooks")
    takeaways = models.ManyToManyField(Takeaway, related_name="playbooks")

    class Meta:
        unique_together = ("title", "project")

    def __str__(self):
        return self.title
