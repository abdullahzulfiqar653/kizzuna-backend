from rest_framework import serializers
from ordered_model.serializers import OrderedModelSerializer

from api.models.takeaway import Takeaway
from api.models.playbook_takeaway import PlaybookTakeaway

from api.serializers.playbook import PlaybookSerializer
from api.serializers.takeaway import TakeawaySerializer


class PlaybookTakeawaySerializer(OrderedModelSerializer, serializers.ModelSerializer):
    takeaway = TakeawaySerializer(read_only=True)
    playbook = PlaybookSerializer(read_only=True)
    takeaway_id = serializers.PrimaryKeyRelatedField(
        source="takeaway", queryset=Takeaway.objects.none(), write_only=True
    )
    order = serializers.IntegerField(required=False)

    class Meta:
        model = PlaybookTakeaway
        fields = ["id", "takeaway_id", "order", "takeaway", "playbook", "start", "end"]
        read_only_fields = ["start", "end"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        playbook = getattr(self.context.get("request"), "playbook", None)
        if playbook:
            self.fields["takeaway_id"].queryset = Takeaway.objects.filter(
                note__in=playbook.notes.all()
            )

    def validate(self, attrs):
        request = self.context.get("request")
        if self.instance is None:
            if request.playbook.takeaways.filter(pk=attrs["takeaway"].pk).exists():
                raise serializers.ValidationError(
                    {"takeaway_id": "Takeaway already exists in playbook"}
                )
        return super().validate(attrs)

    def perform_post_save_actions(self, playbook_takeaway: PlaybookTakeaway):
        playbook_takeaway.playbook.create_playbook_clip_and_thumbnail()
        playbook_takeaway.playbook.update_playbook_takeaway_times()

    def create(self, validated_data):
        playbook = getattr(self.context.get("request"), "playbook")
        validated_data["playbook"] = playbook
        playbook_takeaway = super().create(validated_data)
        self.perform_post_save_actions(playbook_takeaway)

        return playbook_takeaway

    def update(self, instance, validated_data):
        playbook_takeaway = super().update(instance, validated_data)
        self.perform_post_save_actions(playbook_takeaway)
        return playbook_takeaway
