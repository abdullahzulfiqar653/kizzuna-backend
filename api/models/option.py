from django.db import models
from ordered_model.models import OrderedModel
from shortuuid.django_fields import ShortUUIDField

from api.models.property import Property


class Option(OrderedModel):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    property = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="options", editable=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    order_with_respect_to = "property"

    class Meta:
        unique_together = ("name", "property")
        ordering = ("property", "order")

    def __str__(self):
        return f"{self.name}"
