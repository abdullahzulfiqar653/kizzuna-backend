from rest_framework import serializers
from api.models.task import Task


class TaskApprovalSerializer(serializers.Serializer):
    task_ids = serializers.PrimaryKeyRelatedField(
        queryset=Task.objects.all(),
        many=True,
        write_only=True,
        required=False,
        allow_null=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if getattr(request, "note", None):
            self.fields["task_ids"].queryset = request.note.tasks.filter(
                created_by__username="bot@raijin.ai"
            )

    def create(self, validated_data):
        request = self.context.get("request")

        if request.note.is_approved:
            raise serializers.ValidationError({"error": "Note is already approved"})

        request.note.tasks.exclude(
            id__in=[task.id for task in validated_data["task_ids"]]
        ).delete()

        request.note.is_approved = True
        request.note.save()

        return {"status": "Note approved successfully"}
