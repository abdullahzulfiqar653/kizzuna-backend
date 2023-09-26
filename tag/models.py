from django.db import models
from workspace.models import Workspace
from shortuuid.django_fields import ShortUUIDField

class Tag(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    workspaces = models.ManyToManyField(Workspace, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name