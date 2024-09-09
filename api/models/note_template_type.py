from django.db import models
from shortuuid.django_fields import ShortUUIDField


class NoteTemplateType(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    template = models.ForeignKey(
        "api.NoteTemplate", on_delete=models.CASCADE, related_name="types"
    )
    name = models.CharField(max_length=255)
    data = models.JSONField(default=dict)

    class Meta:
        unique_together = ("template", "name")

    def __str__(self):
        return f"Type: {self.name} for Template: {self.template.name}"
