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
    query_field = "vector"

    def get_queryset(self):
        return TakeawaySerializer.optimize_query(
            Takeaway.objects.filter(note__project=self.request.project),
            self.request.user,
        )
