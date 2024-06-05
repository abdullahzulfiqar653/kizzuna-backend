from django.db import models
from ordered_model.models import OrderedModel

from api.models.note_property import NoteProperty
from api.models.option import Option


class NotePropertyOption(OrderedModel):
    note_property = models.ForeignKey(NoteProperty, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order_with_respect_to = "note_property"

    class Meta:
        unique_together = ("note_property", "option")
        ordering = ("note_property", "order")
