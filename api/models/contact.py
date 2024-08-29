from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.organization import Organization
from api.models.project import Project
from api.models.user import User


class Contact(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=255)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="contacts"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="contacts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_contacts"
    )

    class Meta:
        unique_together = [["project", "email"]]
