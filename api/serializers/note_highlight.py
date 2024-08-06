from decimal import Decimal

from rest_framework import exceptions
from rest_framework import serializers
from django.core.files.base import ContentFile

from api.utils import media
from api.ai.embedder import embedder
from api.models.feature import Feature
from api.models.highlight import Highlight
from api.utils.assembly import AssemblyProcessor
from api.serializers.takeaway import TakeawaySerializer
from api.models.usage.transciption import TranscriptionUsage


class NoteHighlightCreateSerializer(TakeawaySerializer):
    end = serializers.IntegerField()
    start = serializers.IntegerField()
    type_id = None

    class Meta:
        model = Highlight
        fields = TakeawaySerializer.Meta.fields
        read_only_fields = list(set(TakeawaySerializer.Meta.fields) - {"start", "end"})

    def validate(self, attrs):
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

        if (
            len(text) > 1000 or clip_length_in_seconds > 300
        ):  # 1000 letters || 5 minutes
            raise exceptions.PermissionDenied(
                "You cannot make a clip greater than 5 minutes."
            )

        # Check workspace-wise audio file limit
        minutes_limit = note.workspace.get_feature_value(
            Feature.Code.DURATION_MINUTE_WORKSPACE
        )
        total_minutes = (note.workspace.usage_seconds + clip_length_in_seconds) / 60

        if total_minutes > minutes_limit:
            raise exceptions.PermissionDenied(
                "You have reached the audio transcription limit "
                "so you can no longer create clips this month. "
                "Your limit will reset in the next month. "
                "Please contact our Support if you still need more assistance."
            )

        TranscriptionUsage.objects.create(
            workspace=note.project.workspace,
            project=note.project,
            note=note,
            created_by=request.user,
            value=clip_length_in_seconds,
            cost=Decimal("0.0001") * round(float(clip_length_in_seconds)),
        )
        (
            clip_content,
            clip_name,
            file_size,
            thumbnail_content,
            thumbnail_name,
            thumbnail_size,
        ) = media.cut_media_file(note.file, start_time, end_time)

        gb_limit = note.workspace.get_feature_value(Feature.Code.STORAGE_GB_WORKSPACE)
        total_bytes = note.workspace.total_file_size + file_size + thumbnail_size
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
            clip_size=file_size,
            thumbnail_size=thumbnail_size,
            **validated_data,
        )

        clip_file = ContentFile(clip_content)
        highlight.clip.save(clip_name, clip_file, save=False)

        if thumbnail_content:
            thumbnail_file = ContentFile(thumbnail_content)
            highlight.thumbnail.save(thumbnail_name, thumbnail_file, save=False)
        highlight.save()
        note.transcript = assembly.update_transcript_highlights(
            validated_data["start"], validated_data["end"], highlight.id
        )  # passing start and end in ms
        note.save(update_fields=["transcript"])

        return highlight
