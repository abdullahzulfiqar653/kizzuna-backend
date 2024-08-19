from rest_framework import serializers

from api.models.note import Note
from api.models.playbook import Playbook


class PlayBookSerializer(serializers.ModelSerializer):
    report_ids = serializers.PrimaryKeyRelatedField(
        source="notes",
        queryset=Note.objects.none(),
        many=True,
        required=False,
    )

    class Meta:
        model = Playbook
        fields = [
            "id",
            "video",
            "title",
            "thumbnail",
            "report_ids",
            "description",
        ]
        read_only_fields = [
            "video",
            "thumbnail",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.get_project()
        if project:
            self.fields["report_ids"].child_relation.queryset = project.notes.all()

    def get_project(self):
        """
        Helper method to retrieve the project from the context.
        """
        request = self.context.get("request")
        if hasattr(request, "project"):
            return request.project
        if hasattr(request, "playbook"):
            return request.playbook.project

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["created_by"] = request.user
        validated_data["project"] = request.project
        return super().create(validated_data)

    def update(self, instance, validated_data):
        notes_data = validated_data.pop("notes", None)
        if notes_data:
            notes_to_add = set(notes_data) - set(instance.notes.all())
            instance.notes.add(*notes_to_add)

        return super().update(instance, validated_data)
