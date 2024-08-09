from rest_framework import generics
from api.filters.takeaway import TakeawayFilter
from api.serializers.playbook_takeaway import PlaybookTakeawaySerializer


class PlaybookVideoTakeawaysListView(generics.ListCreateAPIView):
    serializer_class = PlaybookTakeawaySerializer
    filterset_class = TakeawayFilter
    search_fields = [
        "title",
        "highlight__quote",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]
    ordering = ["created_at"]
    ordering_fields = [
        "created_at",
        "created_by__first_name",
        "created_by__last_name",
        "title",
    ]

    def get_queryset(self):
        return self.request.playbook.takeaways.all()
