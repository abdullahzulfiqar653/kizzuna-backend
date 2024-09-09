from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.contact import Contact
from api.models.integrations.google.calendar.channel import GoogleCalendarChannel


class GoogleCalendarAttendee(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=255)
    channel = models.ForeignKey(
        GoogleCalendarChannel, on_delete=models.CASCADE, related_name="attendees"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    contacts = models.ManyToManyField(Contact, related_name="attendees")

    class Meta:
        unique_together = [["channel", "email"]]

    def __str__(self) -> str:
        return self.name or self.email
