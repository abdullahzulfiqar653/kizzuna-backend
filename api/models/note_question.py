from django.db import models
from ordered_model.models import OrderedModel

from api.models.note import Note
from api.models.question import Question


class NoteQuestion(OrderedModel):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order_with_respect_to = "note"

    class Meta:
        ordering = ("note", "order")
        unique_together = [["note", "question"]]
