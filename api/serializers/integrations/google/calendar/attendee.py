from rest_framework import serializers

from api.models.integrations.google.calendar.attendee import GoogleCalendarAttendee


class GoogleCalendarAttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleCalendarAttendee
        fields = ("id", "email", "name")
        read_only_fields = ("id", "email", "name")
