from django.db import models
from django.db.models import Count
from django.db.models.query import QuerySet
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project


class TagModelManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            .annotate(takeaway_count=Count("takeaways", distinct=True))
        )


class Tag(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=50)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tags")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TagModelManager()

    class Meta:
        unique_together = [["name", "project"]]

    def __str__(self):
        return self.name
