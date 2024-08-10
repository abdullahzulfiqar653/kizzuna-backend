from api.serializers.takeaway import TakeawaySerializer
from api.models.takeaway import Takeaway
from api.models.playbook import PlayBookTakeaway
from rest_framework import serializers, exceptions


class PlaybookTakeawaySerializer(TakeawaySerializer):
    order = serializers.IntegerField(required=False)
    takeaway_id = serializers.CharField(required=False)
    type_id = None

    class Meta:
        model = Takeaway
        fields = TakeawaySerializer.Meta.fields + ["order", "takeaway_id"]
        read_only_fields = list(set(TakeawaySerializer.Meta.fields))

    def validate_takeaway_id(self, takeaway_id):
        request = self.context.get("request")
        if (
            not Takeaway.objects.filter(note__in=request.playbook.notes.all())
            .filter(id=takeaway_id)
            .exists()
        ):
            raise exceptions.NotFound(
                f"Takeaway with ID {takeaway_id} does not exist or does not belong to the user."
            )
        return takeaway_id

    def validate(self, attrs):
        request = self.context.get("request")

        if request.method == "POST":
            if request.playbook.takeaways.filter(pk=attrs["takeaway_id"]).exists():
                raise serializers.ValidationError("Takeaway already exists in playbook")

        return super().validate(attrs)

    def create(self, validated_data):
        request = self.context.get("request")
        return PlayBookTakeaway.objects.create(
            playbook=request.playbook, takeaway_id=validated_data["takeaway_id"]
        )

    def update(self, takeaway, validated_data):
        request = self.context.get("request")
        PlayBookTakeaway.objects.get(playbook=request.playbook, takeaway=takeaway).to(
            validated_data["order"]
        )
        return super().update(request.playbook, validated_data)
