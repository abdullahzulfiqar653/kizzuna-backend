from drf_spectacular.utils import extend_schema
from rest_framework import generics

from api.models.question import Question
from api.serializers.question import QuestionSerializer


@extend_schema(deprecated=True)
class NoteTemplateQuestionListView(generics.ListAPIView):
    queryset = Question.objects.none()
    serializer_class = QuestionSerializer

    def get_queryset(self):
        return self.request.note_template.questions.all()
