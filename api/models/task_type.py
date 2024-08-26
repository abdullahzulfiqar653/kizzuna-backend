from django.db import models
from shortuuid.django_fields import ShortUUIDField
from pgvector.django import HnswIndex, VectorField


default_task_types = [
    {"name": "Bug Fix", "definition": "Fixing bugs or issues in the project."},
    {"name": "Feature", "definition": "Developing new features for the project."},
    {
        "name": "Improvement",
        "definition": "Improving existing features or performance.",
    },
    {"name": "Documentation", "definition": "Writing or updating documentation."},
    {"name": "Code Review", "definition": "Reviewing code submitted by team members."},
    {
        "name": "Testing",
        "definition": "Testing the application for functionality or bugs.",
    },
]


class TaskType(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    definition = models.CharField(max_length=255)
    vector = VectorField(dimensions=1536)

    project = models.ForeignKey(
        "api.Project", on_delete=models.CASCADE, related_name="task_types"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [["project", "name"]]
        indexes = [
            HnswIndex(
                name="task-type-vector-index",
                fields=["vector"],
                opclasses=["vector_ip_ops"],  # Use the inner product operator
            ),
        ]

    def __str__(self) -> str:
        return self.name
