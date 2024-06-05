from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.property import Property


class NoteProperty(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    note = models.ForeignKey(
        "Note", on_delete=models.CASCADE, related_name="note_properties", editable=False
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="note_properties",
        editable=False,
    )
    text_value = models.TextField(blank=True)
    number_value = models.DecimalField(null=True, max_digits=20, decimal_places=10)
    options = models.ManyToManyField(
        "Option", related_name="note_properties", through="NotePropertyOption"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("note", "property")
