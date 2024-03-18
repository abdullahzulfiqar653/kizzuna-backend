from rest_framework import generics

from api.filters.takeaway import TakeawayFilter
from api.models.takeaway import Takeaway
from api.serializers.takeaway import TakeawaySerializer


class ProjectTakeawayListView(generics.ListAPIView):
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
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]

    def get_queryset(self):
        return (
            Takeaway.objects.filter(note__project=self.request.project)
            .select_related("created_by", "type", "note", "question")
            .prefetch_related("tags")
            .only(
                "id",
                "title",
                "type",
                "description",
                "priority",
                "created_by__email",
                "created_by__first_name",
                "created_by__last_name",
                "note__id",
                "note__title",
                "created_at",
                "question__id",
                "question__title",
            )
        )
