from django.utils import timezone
from googleapiclient.discovery import build

from api.integrations.recall import recall
from api.models.integrations.google.calendar.event_attendee import (
    GoogleCalendarEventAttendee,
)


class ChannelSynchronizer:
    def sync(channel):
        from api.models.integrations.google.calendar.event import GoogleCalendarEvent

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
            condition_to_update = lambda event_payload: (
                event_payload.get("status") != "cancelled"
                # We only track non all day events
                and event_payload.get("start", {}).get("dateTime") is not None
                and event_payload.get("end", {}).get("dateTime") is not None
            )
            events_to_create.extend(
                [
                    GoogleCalendarEvent.from_event_payload(channel, event_payload)
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
        channel.sync_token = events.get("nextSyncToken")
        channel.save()

        # Add attendees
        from api.models.integrations.google.calendar.attendee import (
            GoogleCalendarAttendee,
        )

        attendees_to_create = {
            attendee["email"]: GoogleCalendarAttendee(
                name=attendee.get("displayName", ""),
                email=attendee["email"],
                channel=channel,
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

        # Update meeting bot
        from api.models.integrations.recall.bot import RecallBot

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

        return channel
