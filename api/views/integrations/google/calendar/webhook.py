from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, response

from api.models.integrations.google.calendar.channel import GoogleCalendarChannel


@extend_schema_view(
    post=extend_schema(
        description="This endpoint is used to receive Google Calendar webhook events.",
        request=None,
        responses={200: None, 403: None},
    )
)
class GoogleCalendarWebhookCreateView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]

    def create(self, request):
        if request.headers.get("X-Goog-Resource-State") != "exists":
            return response.Response(status=200)
        channel_id = request.headers.get("X-Goog-Channel-ID")
        resource_id = request.headers.get("X-Goog-Resource-ID")
        token = request.headers.get("X-Goog-Channel-Token")
        channel = GoogleCalendarChannel.objects.filter(
            channel_id=channel_id, resource_id=resource_id
        ).first()
        if not channel:
            # We should stop the channel here,
            # but we might not have the correct credentials to do it.
            return response.Response(status=200)
        if token != channel.token.hex:
            print(
                f"Token mismatch for Channel ID: {channel_id}, Resource ID: {resource_id}"
            )
            return response.Response({"message": "Token mismatched"}, status=400)
        channel.sync()

        return response.Response(status=200)
