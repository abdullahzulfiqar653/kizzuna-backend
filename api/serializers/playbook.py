from rest_framework import serializers

from api.models.note import Note
from api.models.playbook import PlayBook


class PlayBookSerializer(serializers.ModelSerializer):
    report_ids = serializers.PrimaryKeyRelatedField(
        source="notes",
        queryset=Note.objects.none(),
        many=True,
        required=False,
    )

    class Meta:
        model = PlayBook
        fields = [
            "id",
            "title",
            "report_ids",
            "description",
        ]

    def get_project(self):
        """
        Helper method to retrieve the project from the context.
        """
        request = self.context.get("request")
        if hasattr(request, "project"):
            return request.project
        if hasattr(request, "playbook"):
            return request.playbook.project

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.get_project()
        if project:
            self.fields["report_ids"].child_relation.queryset = project.notes.all()

    def validate_title(self, title):
        project = self.get_project()
        if self.instance and self.instance.title == title:
            return title  # Title hasn't changed, no need for validation
        if PlayBook.objects.filter(title=title, project=project).exists():
            raise serializers.ValidationError(
                "A PlayBook with this title in the current project already exists."
            )
        return title

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["created_by"] = request.user
        validated_data["workspace"] = request.project.workspace
        validated_data["project"] = request.project
        return super().create(validated_data)

    def update(self, instance, validated_data):
        notes_data = validated_data.pop("notes", None)
        notes_to_add = set(notes_data) - set(instance.notes.all())
        instance.notes.add(*notes_to_add)

        return super().update(instance, validated_data)
