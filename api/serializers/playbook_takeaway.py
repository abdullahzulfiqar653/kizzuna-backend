from api.serializers.takeaway import TakeawaySerializer
from api.models.takeaway import Takeaway
from api.models.playbook import PlayBookTakeaway
from rest_framework import serializers, exceptions
from django.conf import settings
from api.utils.media import merge_media_files


class PlaybookTakeawaySerializer(TakeawaySerializer):
    order = serializers.IntegerField(required=False)
    clip = serializers.SerializerMethodField()
    takeaway_id = serializers.CharField(required=False)
    type_id = None

    class Meta:
        model = Takeaway
        fields = TakeawaySerializer.Meta.fields + ["order", "takeaway_id"]
        read_only_fields = list(set(TakeawaySerializer.Meta.fields))

    def get_clip(self, obj):
        playbook = self.context.get("request").playbook
        return playbook.clip.url

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
        return PlayBookTakeaway.objects.create(
            playbook=request.playbook, takeaway_id=validated_data["takeaway_id"]
        )

    def update(self, takeaway, validated_data):
        request = self.context.get("request")
        PlayBookTakeaway.objects.get(playbook=request.playbook, takeaway=takeaway).to(
            validated_data["order"]
        )
        playbook_takeaways = PlayBookTakeaway.objects.filter(
            takeaway__in=request.playbook.takeaways.all()
        ).order_by("-order")

        urls = "\n".join(
            f"file '{pt.takeaway.highlight.clip.url if settings.USE_S3 else pt.takeaway.highlight.clip.path}'"
            for pt in playbook_takeaways
        )
        request.playbook.clip = merge_media_files(urls)
        request.playbook.save()
        return super().update(request.playbook, validated_data)


# USE S3:
# 6GGpQZFLtv6q
# 6yeHhpcVQGfd

# USE LOCAL:
# GZkgMTwstH9b
# 7TwpAQ3U5uq6
