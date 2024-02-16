from django.db import models
from ordered_model.models import OrderedModel
from shortuuid.django_fields import ShortUUIDField

from api.models.note_template import NoteTemplate
from api.models.question import Question


class NoteTemplateQuestion(OrderedModel):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    note_template = models.ForeignKey(NoteTemplate, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order_with_respect_to = "note_template"

    class Meta:
        ordering = ("note_template", "order")
        unique_together = [["note_template", "question"]]
