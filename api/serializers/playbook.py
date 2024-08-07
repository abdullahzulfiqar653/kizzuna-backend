from rest_framework import serializers

from api.models.note import Note
from api.models.playbook import PlayBook
from api.models.highlight import Highlight


class PlaybookTakeawaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Highlight
        fields = ["id", "clip", "thumbnail"]


class PlayBookSerializer(serializers.ModelSerializer):
    highlights = PlaybookTakeawaySerializer(many=True, read_only=True)

    report_ids = serializers.PrimaryKeyRelatedField(
        source="notes",
        queryset=Note.objects.none(),
        many=True,
        required=False,
    )
    takeaway_ids = serializers.PrimaryKeyRelatedField(
        source="highlights",
        queryset=Highlight.objects.none(),
        many=True,
        required=False,
    )

    class Meta:
        model = PlayBook
        fields = [
            "id",
            "title",
            "highlights",
            "report_ids",
            "description",
            "takeaway_ids",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["takeaways"] = representation.pop("highlights")
        return representation

    def get_project(self):
        """
        Helper method to retrieve the project from the context.
        """
        request = self.context.get("request")
        if hasattr(request, "project"):
            return request.project
        if hasattr(request, "playbook"):
            return request.playbook.project
        raise serializers.ValidationError(
            "Project information is missing in the request context."
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.get_project()
        self.fields["report_ids"].child_relation.queryset = project.notes.all()
        self.fields["takeaway_ids"].child_relation.queryset = Highlight.objects.filter(
            note__id__in=project.notes.values_list("id", flat=True)
        )

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
