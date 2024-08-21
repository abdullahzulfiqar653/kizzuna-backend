from django.db import models
from api.models.playbook import Playbook
from api.models.takeaway import Takeaway
from ordered_model.models import OrderedModel


class PlaybookTakeaway(OrderedModel):
    playbook = models.ForeignKey(
        Playbook, on_delete=models.CASCADE, related_name="playbook_takeaways"
    )
    takeaway = models.ForeignKey(Takeaway, on_delete=models.CASCADE)
    start = models.PositiveIntegerField(null=True)
    end = models.PositiveIntegerField(null=True)
    order_with_respect_to = "playbook"

    class Meta:
        ordering = ["order"]
        unique_together = ("playbook", "takeaway")
