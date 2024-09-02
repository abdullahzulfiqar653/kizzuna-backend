from rest_framework import serializers
from api.models.task_type import TaskType


class TaskTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType
        fields = [
            "id",
            "name",
            "definition",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_project(self):
        """
        Helper method to retrieve the project from the context.
        """
        request = self.context.get("request")
        if hasattr(request, "project"):
            return request.project
        if hasattr(request, "tasktype"):
            return request.tasktype.project

    def validate_name(self, name):
        project = self.get_project()
        if TaskType.objects.filter(name=name, project=project).exists():
            raise serializers.ValidationError(
                f"A task type with name '{name}' already exists in this project."
            )
        return name

    def create(self, validated_data):
        validated_data["project"] = self.context["request"].project
        return super().create(validated_data)
