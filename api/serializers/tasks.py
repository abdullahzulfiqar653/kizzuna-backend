from rest_framework import serializers

from api.models.task import Task
from api.models.user import User
from api.models.task_type import TaskType

from api.ai.embedder import embedder


class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.CharField(source="created_by.first_name", read_only=True)
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    type = serializers.PrimaryKeyRelatedField(
        queryset=TaskType.objects.none(),
        write_only=True,
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
            "last_interaction",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "created_by"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context["request"]
        if hasattr(request, "note"):
            project = request.note.project
            task_types = project.task_types.all()
            workspace_users = User.objects.filter(
                workspace_users__workspace=project.workspace
            ).distinct()
            self.fields["type"].queryset = task_types
            self.fields["assigned_to"].queryset = workspace_users

    def create(self, validated_data):
        validated_data["note"] = self.context["request"].note
        validated_data["created_by"] = self.context["request"].user
        validated_data["vector"] = embedder.embed_documents([validated_data["title"]])[
            0
        ]
        return super().create(validated_data)
