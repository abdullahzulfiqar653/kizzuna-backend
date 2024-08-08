from api.serializers.takeaway import TakeawaySerializer
from api.models.takeaway import Takeaway
from rest_framework import serializers
from api.models.takeaway import Takeaway


class PlaybookTakeawaySerializer(TakeawaySerializer):
    takeaway_ids = serializers.PrimaryKeyRelatedField(
        source="takeaways",
        queryset=Takeaway.objects.none(),
        many=True,
        required=False,
        write_only=True,
    )

    class Meta:
        model = Takeaway
        fields = TakeawaySerializer.Meta.fields + ["takeaway_ids"]
        read_only_fields = list(
            set(TakeawaySerializer.Meta.fields)
            - {
                "takeaway_ids",
            }
        )

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
        request = self.context.get("request")
        self.fields["takeaway_ids"].child_relation.queryset = Takeaway.objects.filter(
            note__in=request.playbook.project.notes.all()
        )

    def update(self, takeaway, validated_data):
        print(validated_data)
        return super().update(takeaway, validated_data)
