import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from googleapiclient.discovery import build
from shortuuid.django_fields import ShortUUIDField

from api.integrations.recall import recall
from api.models.integrations.google.calendar.event_attendee import (
    GoogleCalendarEventAttendee,
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
        old_channel_id = self.channel_id
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
        from api.models.integrations.google.calendar.event import GoogleCalendarEvent

        creds = self.credential.to_credentials()
        calendar = build("calendar", "v3", credentials=creds)
        page_token = None
        events_to_create = []
        event_ids_to_delete = set()

        while True:
            events = (
                calendar.events()
                .list(
                    calendarId="primary",
                    pageToken=page_token,
                    syncToken=self.sync_token,
                    singleEvents=True,
                )
                .execute()
            )
            condition_to_update = lambda event_payload: (
                event_payload.get("status") != "cancelled"
                # We only track non all day events
                and event_payload.get("start", {}).get("dateTime") is not None
                and event_payload.get("end", {}).get("dateTime") is not None
            )
            events_to_create.extend(
                [
                    GoogleCalendarEvent.from_event_payload(self, event_payload)
                    for event_payload in events.get("items", [])
                    if condition_to_update(event_payload) is True
                ]
            )

            # Handle cancelled and all-day events
            event_ids_to_delete |= {
                event_payload["id"]
                for event_payload in events.get("items", [])
                if condition_to_update(event_payload) is False
            }
            # Delete master event when converting single event to recurring event
            event_ids_to_delete |= {
                event_payload["recurringEventId"]
                for event_payload in events.get("items", [])
                if event_payload.get("recurringEventId")
            }

            page_token = events.get("nextPageToken")
            if not page_token:
                break

        all_fields = {
            field.name
            for field in GoogleCalendarEvent._meta.get_fields()
            if field.concrete
        }
        unique_fields = {"channel", "event_id"}
        GoogleCalendarEvent.objects.bulk_create(
            events_to_create,
            update_conflicts=True,
            batch_size=1000,
            unique_fields=unique_fields,
            update_fields=all_fields - unique_fields - {"id", "attendees"},
        )
        self.events.filter(event_id__in=event_ids_to_delete).delete()
        self.sync_token = events.get("nextSyncToken")
        self.save()

        # Add attendees
        from api.models.integrations.google.calendar.attendee import (
            GoogleCalendarAttendee,
        )

        attendees_to_create = {
            attendee["email"]: GoogleCalendarAttendee(
                name=attendee.get("displayName"),
                email=attendee["email"],
                channel=self,
            )
            for event in events_to_create
            for attendee in event.raw.get("attendees", [])
            if attendee.get("self") is not True
        }
        GoogleCalendarAttendee.objects.bulk_create(
            list(attendees_to_create.values()),
            update_conflicts=True,
            batch_size=1000,
            unique_fields={"channel", "email"},
            update_fields={"name"},
        )

        # Add attendees to events
        event_ids = {event.event_id for event in events_to_create}
        events = GoogleCalendarEvent.objects.filter(
            channel=self, event_id__in=event_ids
        )
        attendees_mapping = {
            attendee.email: attendee
            for attendee in GoogleCalendarAttendee.objects.filter(
                channel=self, email__in=attendees_to_create.keys()
            )
        }
        event_attendees_to_create = [
            GoogleCalendarEventAttendee(
                event_id=event.id,
                attendee_id=attendees_mapping[attendee["email"]].id,
                response_status=attendee.get("responseStatus"),
                organizer=attendee.get("organizer", False),
            )
            for event in events
            for attendee in event.raw.get("attendees", [])
            if attendee.get("self") is not True
        ]
        GoogleCalendarEventAttendee.objects.bulk_create(
            event_attendees_to_create,
            ignore_conflicts=True,
            batch_size=1000,
            unique_fields={"event", "attendee"},
        )

        # Update meeting bot
        from api.models.integrations.recall.bot import RecallBot

        event_ids = [event.id for event in events_to_create]
        recall_bots = RecallBot.objects.filter(
            event__channel=self, event_id__in=event_ids
        ).select_related("event")
        recall_bots_to_update = []
        recall_bot_ids_to_delete = []
        for recall_bot in recall_bots:
            if (
                recall_bot.meeting_url != recall_bot.event.meeting_url
                or recall_bot.meeting_platform != recall_bot.event.meeting_platform
                or recall_bot.join_at != recall_bot.event.start
            ):
                recall_bot.meeting_url = recall_bot.event.meeting_url
                recall_bot.meeting_platform = recall_bot.event.meeting_platform
                recall_bot.join_at = recall_bot.event.start
                if recall_bot.meeting_url is None:
                    recall_bot_ids_to_delete.append(recall_bot.id)
                else:
                    recall_bots_to_update.append(recall_bot)
        RecallBot.objects.bulk_update(recall_bots_to_update, ["meeting_url", "join_at"])
        for recall_bot in recall_bots_to_update:
            recall.v1.bot(recall_bot.id).patch(
                meeting_url=recall_bot.meeting_url,
                join_at=recall_bot.join_at.asisoformat(),
            )
        RecallBot.objects.filter(id__in=recall_bot_ids_to_delete).delete()
        for recall_bot_id in recall_bot_ids_to_delete:
            recall.v1.bot(recall_bot_id).delete()
        return self

    def flush(self):
        # This is just for testing purposes
        self.events.all().delete()
        self.sync_token = None
        self.save()
        return self
