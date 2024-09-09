from rest_framework import serializers

from api.models.task import Task
from api.serializers.note import TitleOnlyNoteSerializer
from api.serializers.task_type import TaskTypeSerializer
from api.serializers.user import UserSerializer


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    assignee = serializers.CharField(write_only=True, allow_null=True, required=False)
    report = TitleOnlyNoteSerializer(source="note", read_only=True)

    type = TaskTypeSerializer(required=False)
    created_by = serializers.CharField(source="created_by.first_name", read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "type",
            "title",
            "status",
            "report",
            "assignee",
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

    def validate_assignee(self, value):
        project = self.get_project()
        if value is None:
            return
        user = project.users.filter(username=value).first()
        print(f"value: {value}")
        if not user:
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
        if "assignee" in validated_data:
            validated_data["assigned_to"] = validated_data.pop("assignee")
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "assignee" in validated_data:
            validated_data["assigned_to"] = validated_data.pop("assignee")
        return super().update(instance, validated_data)
