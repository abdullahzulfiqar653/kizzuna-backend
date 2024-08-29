from rest_framework import serializers

from api.models.task import Task
from api.models.user import User
from api.models.task_type import TaskType


class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.first_name", read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.none(),
        required=False,
        allow_null=True,
    )
    type = serializers.PrimaryKeyRelatedField(
        queryset=TaskType.objects.none(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "type",
            "title",
            "status",
            "due_date",
            "priority",
            "created_at",
            "updated_at",
            "created_by",
            "assigned_to",
            "description",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.get_project()
        if project:
            self.fields["type"].queryset = project.task_types.all()
            self.fields["assigned_to"].queryset = User.objects.filter(
                workspace_users__workspace=project.workspace
            )

    def get_project(self):
        """
        Helper method to retrieve the project from the context.
        """
        request = self.context.get("request")
        if hasattr(request, "note"):
            return request.note.project
        if hasattr(request, "task"):
            return request.task.note.project

    def create(self, validated_data):
        validated_data["note"] = self.context["request"].note
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
