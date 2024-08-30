from rest_framework import serializers

from api.models.integrations.google.calendar.event_attendee import (
    GoogleCalendarEventAttendee,
)
from api.serializers.integrations.google.calendar.attendee import (
    GoogleCalendarAttendeeSerializer,
)


class GoogleCalendarEventAttendeeSerializer(serializers.ModelSerializer):
    attendee = GoogleCalendarAttendeeSerializer()

    class Meta:
        model = GoogleCalendarEventAttendee
        fields = ("attendee", "response_status", "organizer")
        read_only_fields = ("attendee", "response_status", "organizer")
