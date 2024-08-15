from django.db import models
from api.models.playbook import PlayBook
from api.models.takeaway import Takeaway
from ordered_model.models import OrderedModel


class PlayBookTakeaway(OrderedModel):
    playbook = models.ForeignKey(
        PlayBook, on_delete=models.CASCADE, related_name="playbook_takeaways"
    )
    takeaway = models.ForeignKey(Takeaway, on_delete=models.CASCADE)
    start = models.PositiveIntegerField(null=True)
    end = models.PositiveIntegerField(null=True)

    class Meta:
        ordering = ["-order"]
        unique_together = ("playbook", "takeaway")
