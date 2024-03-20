from django.db import models
from ordered_model.models import OrderedModel

from api.models.note import Note
from api.models.question import Question
from api.models.user import User


class NoteQuestion(OrderedModel):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order_with_respect_to = "note"
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="note_questions", null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("note", "order")
        unique_together = [["note", "question"]]
