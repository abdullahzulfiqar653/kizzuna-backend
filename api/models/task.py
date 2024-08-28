from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.user import User


class Task(models.Model):
    class Priority(models.TextChoices):
        LOW = "Low"
        MED = "Med"
        HIGH = "High"

    class Status(models.TextChoices):
        TODO = "Todo"
        DONE = "Done"
        OVERDUE = "Overdue"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    type = models.ForeignKey(
        "api.TaskType", on_delete=models.SET_NULL, null=True, related_name="tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_tasks"
    )
    due_date = models.DateField(null=True)
    priority = models.CharField(max_length=4, choices=Priority.choices, null=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.TODO)
    note = models.ForeignKey("api.Note", on_delete=models.CASCADE, related_name="tasks")
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_tasks",
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title
