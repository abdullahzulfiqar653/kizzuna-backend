from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.user import User


class Insight(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="insights"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="insights"
    )
    takeaways = models.ManyToManyField(Takeaway, related_name="insights")
