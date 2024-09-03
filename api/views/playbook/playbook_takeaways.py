from django.db import models
from rest_framework import generics

from api.filters.takeaway import TakeawayFilter
from api.models.takeaway import Takeaway
from api.serializers.takeaway import TakeawaySerializer


class PlaybookTakeawaysListView(generics.ListAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer
    filterset_class = TakeawayFilter
    ordering_fields = [
        "created_at",
        "created_by__first_name",
        "created_by__last_name",
        "title",
    ]
    ordering = ["created_at"]
    search_fields = [
        "title",
        "highlight__quote",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]
    query_field = "vector"

    def get_queryset(self):
        return TakeawaySerializer.optimize_query(
            Takeaway.objects.filter(note__in=self.request.playbook.notes.all()).filter(
                models.Q(note__is_shared=True)
                | models.Q(note__author=self.request.user)
            ),
            self.request.user,
        )
