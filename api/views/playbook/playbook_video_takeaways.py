from rest_framework import generics
from api.filters.takeaway import TakeawayFilter
from api.serializers.takeaway import TakeawaySerializer


class PlaybookVideoTakeawaysListView(generics.ListAPIView):
    serializer_class = TakeawaySerializer
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
        return self.request.playbook.highlights.all()
