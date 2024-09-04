from django.utils import timezone
from googleapiclient.discovery import build

from api.integrations.recall import recall
from api.models.integrations.google.calendar.event_attendee import (
    GoogleCalendarEventAttendee,
)


class ChannelSynchronizer:
    def __init__(self, channel) -> None:
        self.channel = channel

    def condition_to_track(self, event_payload):
        return (
            event_payload.get("status") != "cancelled"
            # We only track non all day events
            and event_payload.get("start", {}).get("dateTime") is not None
            and event_payload.get("end", {}).get("dateTime") is not None
        )

    def list_events(self):
        from api.models.integrations.google.calendar.event import GoogleCalendarEvent

        channel = self.channel
        creds = channel.credential.to_credentials()
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
                    syncToken=channel.sync_token,
                    singleEvents=True,
                )
                .execute()
            )
            events_to_create.extend(
                [
                    GoogleCalendarEvent.from_event_payload(channel, event_payload)
                    for event_payload in events.get("items", [])
                    if self.condition_to_track(event_payload) is True
                ]
            )

            # Handle cancelled and all-day events
            event_ids_to_delete |= {
                event_payload["id"]
                for event_payload in events.get("items", [])
                if self.condition_to_track(event_payload) is False
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

        sync_token = events.get("nextSyncToken")
        return events_to_create, event_ids_to_delete, sync_token

    def sync_events(self):
        from api.models.integrations.google.calendar.event import GoogleCalendarEvent

        channel = self.channel
        events_to_create, event_ids_to_delete, sync_token = self.list_events()

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

        # If user delete an event that already has a bot that has recording,
        # we will keep the bot and remove the event from the bot
        events_to_delete = channel.events.filter(event_id__in=event_ids_to_delete)
        for event in events_to_delete:
            bot = getattr(event, "recall_bot", None)
            if bot is None or bot.join_at < timezone.now():
                continue
            bot.event = None
            bot.save()

        events_to_delete.delete()
        channel.sync_token = sync_token
        channel.save()
        return events_to_create

    def add_attendees(self, events_to_create):
        from api.models.integrations.google.calendar.attendee import (
            GoogleCalendarAttendee,
        )
        from api.models.integrations.google.calendar.event import GoogleCalendarEvent

        channel = self.channel
        attendees_to_create = {
            attendee["email"]: GoogleCalendarAttendee(
                name=attendee.get("displayName", ""),
                email=attendee["email"],
                channel=channel,
            )
            for event in events_to_create
            for attendee in event.raw.get("attendees", [])
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
            channel=channel, event_id__in=event_ids
        )
        attendees_mapping = {
            attendee.email: attendee
            for attendee in GoogleCalendarAttendee.objects.filter(
                channel=channel, email__in=attendees_to_create.keys()
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
        ]
        GoogleCalendarEventAttendee.objects.bulk_create(
            event_attendees_to_create,
            ignore_conflicts=True,
            batch_size=1000,
            unique_fields={"event", "attendee"},
        )

    def get_newly_created_events(self, events_to_create, time_before_sync):
        from api.models.integrations.google.calendar.event import GoogleCalendarEvent

        return GoogleCalendarEvent.objects.filter(
            channel=self.channel, created_at__gt=time_before_sync
        )

    def create_recall_bots(self, newly_created_events):
        from api.models.integrations.recall.bot import RecallBot

        channel = self.channel
        for event in newly_created_events:
            if event.meeting_url is not None:
                RecallBot.objects.create(
                    event=event,
                    project=channel.credential.project,
                    meeting_url=event.meeting_url,
                    meeting_platform=event.meeting_platform,
                    join_at=event.start,
                    created_by=channel.credential.project.created_by,
                )

    def update_recall_bots(self, events_to_create):
        from api.models.integrations.recall.bot import RecallBot

        channel = self.channel
        event_ids = [event.id for event in events_to_create]
        recall_bots = RecallBot.objects.filter(
            event__channel=channel, event_id__in=event_ids
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

        # Update the bots for the events where users have updated the meeting url or start time
        RecallBot.objects.bulk_update(recall_bots_to_update, ["meeting_url", "join_at"])
        for recall_bot in recall_bots_to_update:
            recall.v1.bot(recall_bot.id).patch(
                meeting_url=recall_bot.meeting_url,
                join_at=recall_bot.join_at.asisoformat(),
            )

        # Delete the bots for the events where users have removed the meeting url
        recall_bots_to_delete = RecallBot.objects.filter(
            id__in=recall_bot_ids_to_delete, join_at__gt=timezone.now()
        )
        for recall_bot in recall_bots_to_delete:
            recall.v1.bot(recall_bot.id.hex).delete()
        recall_bots_to_delete.delete()

    def sync(self):
        channel = self.channel
        time_before_sync = timezone.now()
        events_to_create = self.sync_events()
        self.add_attendees(events_to_create)
        newly_created_events = self.get_newly_created_events(
            events_to_create, time_before_sync
        )
        self.create_recall_bots(newly_created_events)
        self.update_recall_bots(events_to_create, time_before_sync)
        return channel
