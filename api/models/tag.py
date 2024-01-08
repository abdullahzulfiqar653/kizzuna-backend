from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project


class Tag(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags")
    takeaway_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["name", "project"]]

    def __str__(self):
        return self.name
