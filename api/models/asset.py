from django.db import models
from django_celery_results.models import TaskResult
from shortuuid.django_fields import ShortUUIDField

from api.models.note import Note
from api.models.project import Project
from api.models.user import User
from api.utils.lexical import blank_content


class Asset(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    title = models.CharField(max_length=255, default="")
    description = models.TextField(default="")
    content = models.JSONField(default=blank_content)
    notes = models.ManyToManyField(Note, related_name="assets")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="assets"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="assets"
    )
    task = models.OneToOneField(TaskResult, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title
