from django.db import models
from api.models.playbook import PlayBook
from api.models.takeaway import Takeaway
from ordered_model.models import OrderedModel


class PlayBookTakeaway(OrderedModel):
    playbook = models.ForeignKey(PlayBook, on_delete=models.CASCADE)
    takeaway = models.ForeignKey(Takeaway, on_delete=models.CASCADE)

    class Meta:
        ordering = ["order"]
        unique_together = ("playbook", "takeaway")
