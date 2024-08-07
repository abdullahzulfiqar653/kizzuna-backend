from rest_framework import serializers

from api.models.note import Note
from api.models.playbook import PlayBook
from api.models.highlight import Highlight


class HighlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Highlight
        fields = ["id", "clip", "thumbnail"]


class PlayBookSerializer(serializers.ModelSerializer):
    takeaways = serializers.SerializerMethodField()
    report_ids = serializers.PrimaryKeyRelatedField(
        source="notes",
        queryset=Note.objects.all(),
        many=True,
        required=False,
    )
    takeaway_ids = serializers.PrimaryKeyRelatedField(
        source="highlights",
        queryset=Highlight.objects.all(),
        many=True,
        required=False,
    )

    def get_takeaways(self, obj):
        takeaways = obj.highlights.all()
        return HighlightSerializer(takeaways, many=True).data

    class Meta:
        model = PlayBook
        fields = [
            "id",
            "title",
            "description",
            "report_ids",
            "takeaway_ids",
            "takeaways",
        ]

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     request = self.context.get("request")
    #     if hasattr(request, "project"):
    #         self.fields["report_ids"].child_relation.queryset = (
    #             request.project.notes.all()
    #         )
    #         self.fields["report_ids"].child_relation.queryset = (
    #             request.project.notes.all()
    #         )

    def validate_title(self, title):
        request = self.context.get("request")
        if hasattr(request, "project"):
            project = request.project
        elif hasattr(request, "playbook"):
            project = request.playbook.project
        if PlayBook.objects.filter(title=title, project=project).exists():
            raise serializers.ValidationError(
                "A PlayBook with this title in current project already exists."
            )
        return title

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["created_by"] = request.user
        validated_data["workspace"] = request.project.workspace
        validated_data["project"] = request.project
        return super().create(validated_data)
