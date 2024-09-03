from rest_framework import serializers

from api.models.task import Task
from api.serializers.user import UserSerializer
from api.serializers.task_type import TaskTypeSerializer


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(required=False, context={"allow_email_write": True})
    type = TaskTypeSerializer()
    created_by = serializers.CharField(source="created_by.first_name", read_only=True)

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

    def get_project(self):
        """
        Helper method to retrieve the project from the context.
        """
        request = self.context.get("request")
        if hasattr(request, "note"):
            return request.note.project
        if hasattr(request, "task"):
            return request.task.note.project

    def validate_assigned_to(self, value):
        email = value.get("email")
        project = self.get_project()
        user = project.users.filter(username=email).first()
        if not email or not user:
            raise serializers.ValidationError(
                f"Assignee User does not exist in project."
            )
        return user

    def validate_type(self, value):
        name = value.get("name")
        project = self.get_project()
        task_type = project.task_types.filter(name=name).first()
        if not task_type:
            raise serializers.ValidationError(f"Task type does not exist in project.")
        return task_type

    def create(self, validated_data):
        validated_data["note"] = self.context["request"].note
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
