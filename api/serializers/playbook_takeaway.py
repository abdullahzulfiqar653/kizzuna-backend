from api.serializers.takeaway import TakeawaySerializer
from api.models.takeaway import Takeaway
from api.models.playbook import PlayBookTakeaway
from rest_framework import serializers


class PlaybookTakeawaySerializer(TakeawaySerializer):
    order = serializers.IntegerField(required=False)
    takeaway_id = serializers.CharField(required=False)
    type_id = None

    class Meta:
        model = Takeaway
        fields = TakeawaySerializer.Meta.fields + ["order", "takeaway_id"]
        read_only_fields = list(set(TakeawaySerializer.Meta.fields))

    def validate(self, attrs):
        if PlayBookTakeaway.objects.filter(takeaway_id=attrs["takeaway_id"]).exists():
            raise serializers.ValidationError("Takeaway already exists in playbook")
        return super().validate(attrs)

    def create(self, validated_data):
        request = self.context.get("request")
        return PlayBookTakeaway.objects.create(
            playbook=request.playbook, takeaway_id=validated_data["takeaway_id"]
        )
