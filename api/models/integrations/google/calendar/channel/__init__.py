import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from googleapiclient.discovery import build
from shortuuid.django_fields import ShortUUIDField

from api.models.integrations.google.calendar.channel.synchronizer import (
    ChannelSynchronizer,
)
from api.models.integrations.google.credential import GoogleCredential


class GoogleCalendarChannel(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    credential = models.ForeignKey(
        GoogleCredential, on_delete=models.CASCADE, related_name="calendar_channels"
    )
    channel_id = models.UUIDField()
    resource_id = models.TextField()
    resource_uri = models.TextField()
    token = models.UUIDField()
    expiration = models.DateTimeField()
    sync_token = models.TextField(null=True)

    class Meta:
        unique_together = ("credential", "id")

    @classmethod
    def create(cls, credential: GoogleCredential):
        creds = credential.to_credentials()
        calendar = build("calendar", "v3", credentials=creds)
        channel_payload = (
            calendar.events()
            .watch(
                calendarId="primary",
                singleEvents=True,
                body={
                    "id": uuid.uuid4().hex,
                    "type": "web_hook",
                    "address": settings.GOOGLE_CALENDAR_WEBHOOK_URL,
                    "token": uuid.uuid4().hex,
                },
            )
            .execute()
        )
        channel = cls.from_channel_payload(credential, channel_payload)
        channel.save()
        return channel

    def refresh(self):
        creds = self.credential.to_credentials()
        old_channel_id = self.channel_id.hex
        old_resource_id = self.resource_id
        calendar = build("calendar", "v3", credentials=creds)
        channel_payload = (
            calendar.events()
            .watch(
                calendarId="primary",
                singleEvents=True,
                body={
                    "id": uuid.uuid4().hex,
                    "type": "web_hook",
                    "address": settings.GOOGLE_CALENDAR_WEBHOOK_URL,
                    "token": uuid.uuid4().hex,
                },
            )
            .execute()
        )
        self.channel_id = channel_payload["id"]
        self.resource_id = channel_payload["resourceId"]
        self.resource_uri = channel_payload["resourceUri"]
        self.token = channel_payload["token"]
        expiration_timestamp = int(channel_payload["expiration"]) / 1000
        self.expiration = timezone.datetime.fromtimestamp(
            expiration_timestamp, tz=timezone.timezone.utc
        )
        self.save()

        # Stop the old channel
        calendar.channels().stop(
            body={"id": old_channel_id, "resourceId": old_resource_id}
        ).execute()
        return self

    @classmethod
    def from_channel_payload(cls, credential, channel_payload):
        expiration_timestamp = (
            int(channel_payload["expiration"]) / 1000
        )  # Convert to seconds
        expiration_datetime = timezone.datetime.fromtimestamp(
            expiration_timestamp, tz=timezone.timezone.utc
        )
        return cls(
            credential=credential,
            channel_id=channel_payload["id"],
            resource_id=channel_payload["resourceId"],
            resource_uri=channel_payload["resourceUri"],
            token=channel_payload.get("token"),
            expiration=expiration_datetime,
        )

    def sync(self):
        return ChannelSynchronizer.sync(self)

    def flush(self):
        # This is just for testing purposes
        self.events.all().delete()
        self.sync_token = None
        self.save()
        return self
