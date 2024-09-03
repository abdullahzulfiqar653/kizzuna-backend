import os
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files.base import File
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, response
from svix.webhooks import Webhook, WebhookVerificationError

from api.integrations.recall import recall
from api.models.integrations.recall.bot import RecallBot
from api.models.note import Note
from api.models.user import User
from api.tasks import analyze_new_note


@extend_schema_view(
    post=extend_schema(
        description="This endpoint is used to receive Recall webhook events.",
        request=None,
        responses={200: None, 403: None},
    )
)
class RecallWebhookCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        try:
            wh = Webhook(settings.RECALLAI_WEBHOOK_SECRET)
            msg = wh.verify(request.body, request.headers)
        except WebhookVerificationError as e:
            return response.Response(str(e), status=403)

        if request.data.get("event") == "bot.status_change":
            bot_id = request.data.get("data").get("bot_id")
            bot = RecallBot.objects.filter(id=bot_id).first()
            if bot is None:
                return response.Response(status=200)

            payload = recall.v1.bot(bot.id.hex).get()
            project_id = payload.get("metadata", {}).get("project_id")
            username = payload.get("metadata", {}).get("created_by")
            recall_env = payload.get("metadata", {}).get("recall_env")
            if recall_env != settings.RECALLAI_ENV:
                return response.Response(status=200)

            bot.status_code = request.data.get("data").get("status").get("code")
            bot.status_sub_code = request.data.get("data").get("status").get("sub_code")
            bot.status_message = request.data.get("data").get("status").get("message")
            created_at = request.data.get("data").get("status").get("created_at")
            bot.status_created_at = timezone.datetime.fromisoformat(created_at)
            bot.save()

            user = User.objects.filter(username=username).first()
            if user is None:
                return response.Response(status=200)

            # Handling different status codes
            if (
                request.data.get("data").get("status").get("code")
                == "in_call_recording"
            ):
                name = user.google_credential.get_userinfo().get("name")
                recall.v1.bot(bot.id.hex)("send_chat_message").post(
                    to="everyone",
                    message=f"Hi everyone, I am recording the meeting for {name}",
                )

            if (
                request.data.get("data").get("status").get("code") == "done"
                and getattr(bot, "note", None) is None
            ):
                video_url = payload.get("video_url")

                if video_url is None or project_id is None or username is None:
                    return response.Response(status=200)

                res = requests.get(video_url, stream=True)
                res.raise_for_status()

                # Get the file extension from the video_url
                parsed_url = urlparse(video_url)
                file_extension = os.path.splitext(parsed_url.path)[1]

                # Save the streamed content to a file-like object
                if bot.event and bot.event.summary:
                    title = bot.event.summary
                    file_name = f"{bot.event.summary}{file_extension}"
                else:
                    title = f"Meeting recorded by Kizunna bot"
                    file_name = f"meeting_video{file_extension}"
                video_content = File(res.raw, name=file_name)

                note = Note.objects.create(
                    project_id=project_id,
                    author=user,
                    title=title,
                    content="Recall meeting video",
                    file=video_content,
                    recall_bot=bot,
                )
                analyze_new_note.delay_on_commit(note.id, user.id)

                transcript = recall.v1.bot(bot.id.hex).transcript.get()
                bot.transcript = transcript
                bot.meeting_participants = payload.get("meeting_participants")
                bot.save()

        return response.Response(status=200)
