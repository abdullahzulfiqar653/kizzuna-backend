from django.db import models

from api.models.integrations.google.calendar.event import GoogleCalendarEvent
from api.models.project import Project
from api.models.user import User


class RecallBot(models.Model):
    class StatusCode(models.TextChoices):
        # Ref: https://docs.recall.ai/docs/bot-status-change-events#events
        READY = "ready"
        JOINING_CALL = "joining_call"
        IN_WAITING_ROOM = "in_waiting_room"
        PARTICIPANT_IN_WAITING_ROOM = "participant_in_waiting_room"
        IN_CALL_NOT_RECORDING = "in_call_not_recording"
        RECORDING_PERMISSION_ALLOWED = "recording_permission_allowed"
        RECORDING_PERMISSION_DENIED = "recording_permission_denied"
        IN_CALL_RECORDING = "in_call_recording"
        CALL_ENDED = "call_ended"
        RECORDING_DONE = "recording_done"
        DONE = "done"
        FATAL = "fatal"
        ANALYSIS_DONE = "analysis_done"
        ANALYSIS_FAILED = "analysis_failed"
        MEDIA_EXPIRED = "media_expired"

    id = models.UUIDField(primary_key=True)
    event = models.OneToOneField(
        GoogleCalendarEvent,
        on_delete=models.CASCADE,
        related_name="recall_bot",
        null=True,
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="recall_bots"
    )
    meeting_url = models.URLField(max_length=2000)
    join_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recall_bots"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meeting_platform = models.TextField(
        choices=GoogleCalendarEvent.MeetingPlatform.choices
    )
    meeting_participants = models.JSONField(null=True)
    status_code = models.TextField(choices=StatusCode.choices, null=True)
    status_sub_code = models.TextField(null=True)
    status_message = models.TextField(null=True)
    status_created_at = models.DateTimeField(null=True)
    transcript = models.JSONField(null=True)
