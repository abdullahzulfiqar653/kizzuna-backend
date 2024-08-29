from rest_framework import generics, permissions

from api.filters.integrations.google.calendar.event import GoogleCalendarEventFilter
from api.models.integrations.google.calendar.event import GoogleCalendarEvent
from api.serializers.integrations.google.calendar.event import (
    GoogleCalendarEventSerializer,
)


class GoogleCalendarEventListView(generics.ListAPIView):
    queryset = GoogleCalendarEvent.objects.all()
    serializer_class = GoogleCalendarEventSerializer
    filterset_class = GoogleCalendarEventFilter
    ordering_fields = [
        "start",
        "end",
        "summary",
    ]
    ordering = ["start"]
    search_fields = [
        "summary",
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return GoogleCalendarEvent.objects.filter(
            channel__credential__user=self.request.user
        ).select_related("recall_bot__project__workspace")
