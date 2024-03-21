from django.conf import settings
from rest_framework import exceptions, generics, response, status

from api.models.question import Question
from api.models.takeaway import Takeaway
from api.serializers.question import (
    QuestionRemainingQuotaSerializer,
    QuestionSerializer,
)
from api.tasks import ask_note_question


class NoteQuestionListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = QuestionSerializer

    def get_queryset(self):
        return self.request.note.questions.all()

    def create(self, request, report_id):
        if (
            self.request.note.questions.through.objects.filter(
                created_by=self.request.user
            ).count()
            >= settings.NOTE_QUESTION_QUOTA
        ):
            raise exceptions.PermissionDenied(
                "You have reached your quota limit and "
                "cannot create more questions for this source."
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = Question.objects.create(
            project=self.request.note.project, title=serializer.data["title"]
        )
        self.request.note.questions.add(
            question, through_defaults={"created_by": self.request.user}
        )
        response_serializer = self.get_serializer(question)
        ask_note_question.delay(self.request.note.id, question.id, self.request.user.id)
        return response.Response(
            response_serializer.data, status=status.HTTP_201_CREATED
        )


class NoteQuestionRemainingQuotaRetreiveView(generics.RetrieveAPIView):
    serializer_class = QuestionRemainingQuotaSerializer

    def get_object(self):
        used_quota = self.request.note.questions.through.objects.filter(
            created_by=self.request.user
        ).count()
        return {"value": settings.NOTE_QUESTION_QUOTA - used_quota}
