from django.conf import settings
from rest_framework import exceptions, serializers

from api.integrations.recall import recall
from api.models.integrations.recall.bot import RecallBot
from api.serializers.project import ProjectSerializer


class RecallBotSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    meeting_url = serializers.URLField(required=False)

    class Meta:
        model = RecallBot
        fields = (
            "id",
            "event",
            "project",
            "meeting_url",
            "join_at",
            "status_code",
            "status_sub_code",
            "status_message",
            "status_created_at",
        )
        read_only_fields = (
            "id",
            "project",
            "join_at",
            "status_code",
            "status_sub_code",
            "status_message",
            "status_created_at",
        )

    def validate_event(self, event):
        request = self.context.get("request")
        if event.channel.credential.user != request.user:
            raise exceptions.NotFound("Event does not exist.")
        if event.meeting_url is None:
            raise serializers.ValidationError("Event does not have a meeting URL.")
        if request.user.recall_bots.filter(event=event).exists():
            raise serializers.ValidationError("Bot already exists for this event.")
        return event

    def validate_meeting_url(self, meeting_url):
        request = self.context.get("request")
        if request.user.recall_bots.filter(meeting_url=meeting_url).exists():
            raise serializers.ValidationError(
                "Bot already exists for this meeting URL."
            )
        return meeting_url

    def validate(self, attrs):
        if attrs.get("event") is None and attrs.get("meeting_url") is None:
            raise serializers.ValidationError(
                "Either event or meeting_url must be provided."
            )
        return super().validate(attrs)

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["project"] = request.project
        validated_data["created_by"] = request.user

        # Set meeting_url and join_at if event is provided
        if validated_data.get("event") is not None:
            validated_data["meeting_url"] = validated_data["event"].meeting_url
            validated_data["join_at"] = validated_data["event"].start

        # Create Recall bot
        payload = recall.v1.bot.post(
            meeting_url=validated_data["meeting_url"],
            bot_name=f"{request.user.first_name} Kizunna Notetaker",
            transcription_options=dict(provider="meeting_captions"),
            join_at=(
                validated_data["join_at"].isoformat()
                if validated_data.get("join_at")
                else None
            ),
            metadata=dict(
                project_id=validated_data["project"].id,
                created_by=request.user.username,
                recall_env=settings.RECALLAI_ENV,
                username=request.user.username,
            ),
        )
        validated_data["id"] = payload["id"]

        validated_data["status_code"] = payload.get("status", {}).get("code")
        validated_data["status_sub_code"] = payload.get("status", {}).get("sub_code")
        validated_data["status_message"] = payload.get("status", {}).get("message")
        validated_data["status_created_at"] = payload.get("status", {}).get(
            "created_at"
        )
        return RecallBot.objects.create(**validated_data)
