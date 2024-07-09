from django.db import models
from ordered_model.models import OrderedModel

from api.models.block import Block


class Theme(OrderedModel):
    id = models.AutoField(primary_key=True)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name="themes")
    title = models.CharField(max_length=255)
    takeaways = models.ManyToManyField("Takeaway", related_name="themes")
    order_with_respect_to = "block"

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("block", "order")
        unique_together = ("block", "title")
