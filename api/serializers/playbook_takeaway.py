from rest_framework import serializers
from ordered_model.serializers import OrderedModelSerializer
from api.utils import media
from api.models.takeaway import Takeaway
from api.models.playbook_takeaway import PlayBookTakeaway
from api.serializers.playbook import PlayBookSerializer
from api.models.playbook_takeaway import PlayBookTakeaway
from api.serializers.takeaway import TakeawaySerializer


def create_playbook_clip_and_thumbnail(playbook):
    files = [
        pt.takeaway.highlight.clip
        for pt in PlayBookTakeaway.objects.filter(
            takeaway__in=playbook.takeaways.all()
        ).order_by("-order")
    ]
    clip = media.merge_media_files(files)
    playbook.clip = clip
    playbook.save()
    playbook.thumbnail = media.create_thumbnail(playbook.clip, 1)
    playbook.save()


class PlaybookTakeawaySerializer(OrderedModelSerializer, serializers.ModelSerializer):
    takeaway = TakeawaySerializer(read_only=True)
    playbook = PlayBookSerializer(read_only=True)
    takeaway_id = serializers.PrimaryKeyRelatedField(
        source="takeaway", queryset=Takeaway.objects.none(), write_only=True
    )
    order = serializers.IntegerField(required=False)

    class Meta:
        model = PlayBookTakeaway
        fields = ["takeaway_id", "order", "takeaway", "playbook"]

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
                raise serializers.ValidationError("Takeaway already exists in playbook")
        return super().validate(attrs)

    def create(self, validated_data):
        request = self.context.get("request")
        playbook_takeaway = PlayBookTakeaway.objects.create(
            playbook=request.playbook, takeaway=validated_data["takeaway"]
        )
        create_playbook_clip_and_thumbnail(request.playbook)
        return playbook_takeaway
