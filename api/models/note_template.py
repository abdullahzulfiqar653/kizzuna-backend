from django.db import models
from shortuuid.django_fields import ShortUUIDField

default_templates = [
    {"name": "Basic Meeting", "types": ["Summary", "KeyPoints", "Next Steps"]},
    {
        "name": "Sales Discovery",
        "types": [
            "Next Steps",
            "Competition",
            "Customer Needs",
            "Customer Budget",
            "Sales Meeting Outcome",
        ],
    },
    {
        "name": "Sales Follow-Up",
        "types": ["Deal Timing", "Pricing Feedback", "Sales Meeting Outcome"],
    },
    {
        "name": "Customer Feedback",
        "types": ["Summary", "Next Steps", "Customer Praise", "Customer Pain Points"],
    },
    {
        "name": "Partner Checkin",
        "types": [
            "Summary",
            "Next Steps",
            "Metrics Review",
            "Critical Risks",
            "Customer Satisfaction",
            "Opportunities & Advice",
        ],
    },
]


class NoteTemplate(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    note = models.ForeignKey(
        "api.Note", on_delete=models.CASCADE, related_name="templates"
    )
    name = models.CharField(max_length=255)  # Template name, e.g., "basic meeting"

    class Meta:
        unique_together = ("note", "name")  # Ensure unique template name for each note

    def __str__(self):
        return f"Template: {self.name} for Note: {self.note.title}"
