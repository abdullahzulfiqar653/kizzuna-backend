from rest_framework import serializers

from api.models.integrations.google.calendar.event import GoogleCalendarEvent
from api.serializers.integrations.google.calendar.event_attendee import (
    GoogleCalendarEventAttendeeSerializer,
)
from api.serializers.integrations.recall.bot import RecallBotSerializer


class GoogleCalendarEventSerializer(serializers.ModelSerializer):
    recall_bot = RecallBotSerializer(read_only=True)
    event_attendees = GoogleCalendarEventAttendeeSerializer(many=True, read_only=True)

    class Meta:
        model = GoogleCalendarEvent
        fields = (
            "id",
            "channel_id",
            "ical_uid",
            "summary",
            "status",
            "start",
            "end",
            "html_link",
            "meeting_url",
            "meeting_platform",
            "recall_bot",
            "event_attendees",
        )
        read_only_fields = (
            "id",
            "channel_id",
            "ical_uid",
            "summary",
            "status",
            "start",
            "end",
            "html_link",
            "meeting_url",
            "meeting_platform",
            "recall_bot",
            "event_attendees",
        )
