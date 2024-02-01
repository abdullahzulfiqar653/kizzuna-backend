from django.db import models
from django.utils.text import slugify
from shortuuid.django_fields import ShortUUIDField

from api.models.user import User


class Workspace(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    owned_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_workspaces"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    logo_url = models.URLField(blank=True)
    domain_slug = models.SlugField(max_length=50, unique=True)

    members = models.ManyToManyField(User, related_name="workspaces")

    def __str__(self):
        return f"{self.id} - {self.name}"

    def save(self, *args, **kwargs):
        # Generate the domain slug based on the workspace name
        self.domain_slug = slugify(self.name)
        super().save(*args, **kwargs)
