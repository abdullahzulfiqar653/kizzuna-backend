from django.db import models
from shortuuid.django_fields import ShortUUIDField


default_task_types = [
    {
        "name": "Follow-Up Email",
        "definition": "Sending a follow-up email to a client or stakeholder.",
    },
    {
        "name": "Schedule Appointment",
        "definition": "Arranging and scheduling an appointment or meeting.",
    },
    {
        "name": "Send Attachment",
        "definition": "Sending relevant documents or files as an attachment.",
    },
    {
        "name": "Miscellaneous",
        "definition": "Handling any tasks that don't fit into specific categories.",
    },
]


class TaskType(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    definition = models.CharField(max_length=255, null=True)
    project = models.ForeignKey(
        "api.Project", on_delete=models.CASCADE, related_name="task_types"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["project", "name"]]

    def __str__(self) -> str:
        return self.name
