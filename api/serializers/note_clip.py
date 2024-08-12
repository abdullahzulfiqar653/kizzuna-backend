from rest_framework import exceptions, serializers

from api.ai.embedder import embedder
from api.models.feature import Feature
from api.models.highlight import Highlight
from api.models.note import Note
from api.serializers.takeaway import TakeawaySerializer
from api.utils import media
from api.utils.assembly import AssemblyProcessor


class NoteClipCreateSerializer(TakeawaySerializer):
    end = serializers.IntegerField()
    start = serializers.IntegerField()
    type_id = None

    class Meta:
        model = Highlight
        fields = TakeawaySerializer.Meta.fields
        read_only_fields = list(set(TakeawaySerializer.Meta.fields) - {"start", "end"})

    def validate(self, attrs):
        note = self.context.get("request").note
        if note.media_type not in {Note.MediaType.AUDIO, Note.MediaType.VIDEO}:
            raise exceptions.PermissionDenied(
                "Only supports for audio and video reports."
            )
        if attrs["start"] > attrs["end"]:
            raise serializers.ValidationError(
                {"end": "End time must be after start time."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        note = request.note
        assembly = AssemblyProcessor(note.transcript)

        clip_length_in_seconds = (
            validated_data["end"] - validated_data["start"]
        ) / 1000.0  # getting in seconds
        start_time = validated_data["start"] / 1000  # getting in seconds
        end_time = validated_data["end"] / 1000  # getting in seconds

        text = assembly.get_text_in_range(
            validated_data["start"], validated_data["end"]
        )  # passing start and end in ms

        # TODO: Set the text length and clip length limits in Feature
        if len(text) > 1000:
            raise exceptions.PermissionDenied(
                "You cannot make a highlight greater than 1000 characters"
            )

        if clip_length_in_seconds > 300:  # 5 minutes
            raise exceptions.PermissionDenied(
                "You cannot make a clip greater than 5 minutes."
            )

        clip = media.cut_media_file(note.file, start_time, end_time)
        if note.media_type == Note.MediaType.VIDEO:
            thumbnail = media.create_thumbnail(note.file, start_time)
            thumbnail_size = thumbnail.size
        else:  # audio
            thumbnail = None
            thumbnail_size = 0

        gb_limit = note.workspace.get_feature_value(Feature.Code.STORAGE_GB_WORKSPACE)
        total_bytes = note.workspace.total_file_size + clip.size + thumbnail_size
        total_gbs = total_bytes / 1024 / 1024 / 1024
        if total_gbs > gb_limit:
            raise exceptions.PermissionDenied(
                f"You have reached the storage limit of {gb_limit} GB."
            )

        highlight = Highlight(
            id=Highlight.id.field._generate_uuid(),
            title=text,
            vector=embedder.embed_documents([text])[0],
            created_by=request.user,
            note=note,
            quote=text,
            clip=clip,
            clip_size=clip.size,
            thumbnail=thumbnail,
            thumbnail_size=thumbnail_size,
            **validated_data,
        )
        highlight.save()
        note.transcript = assembly.update_transcript_highlights(
            validated_data["start"], validated_data["end"], highlight.id
        )  # passing start and end in ms
        note.save(update_fields=["transcript"])

        return highlight
