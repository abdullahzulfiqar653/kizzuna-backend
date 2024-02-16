from rest_framework import serializers

from api.models.question import Question


class QuestionSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Question
        fields = ["id", "title"]
