from django.core import serializers
from django.core.management.base import BaseCommand

from api.models.note_template import NoteTemplate
from api.models.note_template_question import NoteTemplateQuestion
from api.models.question import Question


class Command(BaseCommand):
    help = "Dump public note templates data."

    def handle(self, *args, **options):
        data = []
        note_templates = NoteTemplate.objects.filter(project=None)
        data.extend(list(note_templates))

        questions = Question.objects.filter(project=None)
        data.extend(list(questions))

        note_template_questions = NoteTemplateQuestion.objects.filter(
            note_template__in=note_templates, question__in=questions
        )
        data.extend(list(note_template_questions))
        return serializers.serialize("yaml", data)
