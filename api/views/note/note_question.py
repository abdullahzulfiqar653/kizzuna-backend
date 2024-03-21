from django.conf import settings
from rest_framework import exceptions, generics, response, status

from api.models.note import Note
from api.models.note_question import NoteQuestion
from api.models.question import Question
from api.models.takeaway import Takeaway
from api.models.user import User
from api.serializers.question import (
    QuestionRemainingQuotaSerializer,
    QuestionSerializer,
)
from api.tasks import ask_note_question


def get_remaining_quota(note: Note, user: User):
    used_quota = NoteQuestion.objects.filter(note=note, created_by=user).count()
    return max(settings.NOTE_QUESTION_QUOTA - used_quota, 0)


class NoteQuestionListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = QuestionSerializer

    def get_queryset(self):
        return self.request.note.questions.all()

    def create(self, request, report_id):
        # Verify if the user has the quota to ask question
        remaining_quota = get_remaining_quota(self.request.note, self.request.user)
        if remaining_quota <= 0:
            raise exceptions.PermissionDenied(
                "You have reached your quota limit and "
                "cannot create more questions for this source."
            )

        # Create the question if it hasn't been created before
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question, created = Question.objects.get_or_create(
            project=self.request.note.project, title=serializer.data["title"]
        )
        if self.request.note.questions.contains(question):
            raise exceptions.ValidationError(
                {"title": ["Question has been asked before."]}
            )
        self.request.note.questions.add(
            question, through_defaults={"created_by": self.request.user}
        )

        # Send the celery task and return a response
        ask_note_question.delay(self.request.note.id, question.id, self.request.user.id)
        response_serializer = self.get_serializer(question)
        return response.Response(
            response_serializer.data, status=status.HTTP_201_CREATED
        )


class NoteQuestionRemainingQuotaRetreiveView(generics.RetrieveAPIView):
    serializer_class = QuestionRemainingQuotaSerializer

    def get_object(self):
        return {"value": get_remaining_quota(self.request.note, self.request.user)}
