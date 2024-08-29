from django.core.validators import URLValidator
from django.db import models
from django.utils import timezone
from shortuuid.django_fields import ShortUUIDField

from api.models.integrations.google.calendar.attendee import GoogleCalendarAttendee
from api.models.integrations.google.calendar.channel import GoogleCalendarChannel


class GoogleCalendarEvent(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed"
        TENTATIVE = "tentative"
        CANCELLED = "cancelled"

    class MeetingPlatform(models.TextChoices):
        GOOGLE_MEET = "google_meet"
        ZOOM = "zoom"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    channel = models.ForeignKey(
        GoogleCalendarChannel, on_delete=models.CASCADE, related_name="events"
    )
    # Ref: https://stackoverflow.com/questions/73259055/is-the-icaluid-of-an-event-on-google-calendar-unique-for-all-google-accounts
    ical_uid = models.TextField(
        help_text="Google Calendar iCal UID, same for all recurring events"
    )
    event_id = models.TextField(
        help_text="Google Calendar Event ID, different for each recurring event"
    )
    etag = models.TextField(null=True)
    summary = models.TextField(null=True)
    start = models.DateTimeField()
    end = models.DateTimeField()
    status = models.TextField()
    recurring_event_id = models.TextField(null=True)
    html_link = models.URLField(null=True, max_length=2000)
    meeting_url = models.URLField(null=True)
    meeting_platform = models.TextField(null=True, choices=MeetingPlatform.choices)
    raw = models.JSONField(null=True)
    attendees = models.ManyToManyField(
        GoogleCalendarAttendee,
        related_name="events",
        through="GoogleCalendarEventAttendee",
    )

    class Meta:
        unique_together = ("channel", "event_id")

    @classmethod
    def from_event_payload(cls, channel, event_payload):
        meeting_url, meeting_platform = get_conference_details(event_payload)
        return cls(
            channel=channel,
            summary=event_payload.get("summary"),
            start=timezone.datetime.fromisoformat(event_payload["start"]["dateTime"]),
            end=timezone.datetime.fromisoformat(event_payload["end"]["dateTime"]),
            status=event_payload.get("status", cls.Status.CONFIRMED),
            recurring_event_id=event_payload.get("recurringEventId"),
            html_link=event_payload.get("htmlLink"),
            ical_uid=event_payload["iCalUID"],
            event_id=event_payload["id"],
            etag=event_payload.get("etag"),
            meeting_url=meeting_url,
            meeting_platform=meeting_platform,
            raw=event_payload,
        )


def get_conference_details(event_payload):
    # Get Google Meet
    conference_id = (
        event_payload.get("conferenceData", {}).get("conferenceId")
        if event_payload.get("conferenceData", {})
        .get("conferenceSolution", {})
        .get("key", {})
        .get("type")
        == "hangoutsMeet"
        else None
    )
    if conference_id is not None:
        meeting_url = f"https://meet.google.com/{conference_id}"
        meeting_platform = GoogleCalendarEvent.MeetingPlatform.GOOGLE_MEET
        return meeting_url, meeting_platform

    # Get Zoom
    location = event_payload.get("location")
    url_validator = URLValidator()
    try:
        url_validator(location)
    except:
        return None, None
    if location is not None and "zoom.us" in location:
        meeting_url = location
        meeting_platform = GoogleCalendarEvent.MeetingPlatform.ZOOM

    return None, None
