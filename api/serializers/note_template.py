from rest_framework import serializers

from api.models.note_template import NoteTemplate
from api.models.question import Question
from api.serializers.question import QuestionSerializer


class NoteTemplateSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = NoteTemplate
        fields = [
            "id",
            "title",
            "description",
        ]


class NoteTemplateCreateSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    questions = QuestionSerializer(many=True)

    class Meta:
        model = NoteTemplate
        fields = [
            "id",
            "title",
            "description",
            "questions",
        ]

    def create(self, validated_data):
        request = self.context.get("request")
        questions = validated_data.pop("questions", [])
        note_template = NoteTemplate.objects.create(
            **validated_data, project=request.project
        )
        questions_to_create = [
            Question(**question, project=request.project) for question in questions
        ]
        Question.objects.bulk_create(questions_to_create, ignore_conflicts=True)
        questions_to_add = Question.objects.filter(project=request.project).filter(
            title__in=[question["title"] for question in questions]
        )
        note_template.questions.add(*questions_to_add)
        return note_template
