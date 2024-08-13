from django.conf import settings
from rest_framework import serializers, exceptions

from api.utils import media
from api.models.takeaway import Takeaway
from api.models.playbook import PlayBookTakeaway
from api.serializers.takeaway import TakeawaySerializer


def create_playbook_clip_and_thumbnail(playbook):
    playbook_takeaways = PlayBookTakeaway.objects.filter(
        takeaway__in=playbook.takeaways.all()
    ).order_by("-order")
    urls = "\n".join(
        f"file '{pt.takeaway.highlight.clip.url if settings.USE_S3 else pt.takeaway.highlight.clip.path}'"
        for pt in playbook_takeaways
    )
    clip = media.merge_media_files(urls)
    playbook.clip = clip
    playbook.save()
    playbook.thumbnail = media.create_thumbnail(playbook.clip, 1)
    playbook.save()


class PlaybookTakeawaySerializer(TakeawaySerializer):
    clip = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    order = serializers.IntegerField(required=False)
    takeaway_id = serializers.CharField(required=False)
    type_id = None

    class Meta:
        model = Takeaway
        fields = TakeawaySerializer.Meta.fields + ["order", "takeaway_id"]
        read_only_fields = list(set(TakeawaySerializer.Meta.fields))

    def get_clip(self, obj):
        playbook = self.context.get("request").playbook
        return playbook.clip.url if playbook.clip else None

    def get_thumbnail(self, obj):
        playbook = self.context.get("request").playbook
        return playbook.thumbnail.url if playbook.thumbnail else None

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
        if self.instance is None:
            if request.playbook.takeaways.filter(pk=attrs["takeaway_id"]).exists():
                raise serializers.ValidationError("Takeaway already exists in playbook")

        return super().validate(attrs)

    def create(self, validated_data):
        request = self.context.get("request")
        playbook_takeaway = PlayBookTakeaway.objects.create(
            playbook=request.playbook, takeaway_id=validated_data["takeaway_id"]
        )
        create_playbook_clip_and_thumbnail(request.playbook)
        return playbook_takeaway

    def update(self, takeaway, validated_data):
        request = self.context.get("request")
        PlayBookTakeaway.objects.get(playbook=request.playbook, takeaway=takeaway).to(
            validated_data["order"]
        )
        create_playbook_clip_and_thumbnail(request.playbook)
        return super().update(request.playbook, validated_data)
