from django.db import models
from shortuuid.django_fields import ShortUUIDField


class GoogleCalendarEventAttendee(models.Model):
    class ResponseStatus(models.TextChoices):
        NEEDS_ACTION = "needsAction"
        DECLINED = "declined"
        TENTATIVE = "tentative"
        ACCEPTED = "accepted"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    event = models.ForeignKey(
        "GoogleCalendarEvent", on_delete=models.CASCADE, related_name="event_attendees"
    )
    attendee = models.ForeignKey(
        "GoogleCalendarAttendee",
        on_delete=models.CASCADE,
        related_name="event_attendees",
    )
    response_status = models.TextField(choices=ResponseStatus.choices)
    organizer = models.BooleanField(default=False)

    class Meta:
        unique_together = [["event", "attendee"]]
