from rest_framework import exceptions, generics, status
from rest_framework.response import Response

from takeaway.filters import TakeawayFilter
from takeaway.models import Insight, Takeaway
from takeaway.serializers import InsightTakeawaysSerializer, TakeawaySerializer


class InsightTakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
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

    def get_serializer_class(self):
        if self.request.method == "GET":
            return TakeawaySerializer
        elif self.request.method in ("POST", "DELETE"):
            return InsightTakeawaysSerializer
        else:
            raise exceptions.MethodNotAllowed("Only GET, POST and DELETE are allowed.")

    def get_insight(self, insight_id):
        insight = Insight.objects.filter(
            id=insight_id, project__users=self.request.user
        ).first()
        if insight is None:
            raise exceptions.NotFound("Insight not found.")
        return insight

    def get_queryset(self):
        insight = self.get_insight(self.kwargs["insight_id"])
        return insight.takeaways.all()

    def get_valid_takeaways(self, insight: Insight):
        # Can add or remove any takeaways in the project to the insight
        return Takeaway.objects.filter(note__project=insight.project)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        insight = self.get_insight(self.kwargs["insight_id"])
        valid_takeaways = self.get_valid_takeaways(insight)
        context["insight"] = insight
        context["valid_takeaway_ids"] = valid_takeaways.values_list("id", flat=True)
        return context


class InsightTakeawayDeleteView(generics.GenericAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = InsightTakeawaysSerializer

    def get_insight(self, insight_id) -> Insight:
        insight = Insight.objects.filter(
            id=insight_id, project__users=self.request.user
        ).first()
        if insight is None:
            raise exceptions.NotFound("Insight not found.")
        return insight

    def get_valid_takeaways(self, insight: Insight):
        # Can add or remove any takeaways in the project to the insight
        return Takeaway.objects.filter(note__project=insight.project)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        insight = self.get_insight(self.kwargs["insight_id"])
        valid_takeaways = self.get_valid_takeaways(insight)
        context["insight"] = insight
        context["valid_takeaway_ids"] = valid_takeaways.values_list("id", flat=True)
        return context

    def post(self, request, insight_id):
        insight = Insight.objects.filter(
            id=insight_id, project__users=request.user
        ).first()
        if insight is None:
            raise exceptions.NotFound("Insight not found.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.delete()
        return Response(serializer.data, status=status.HTTP_200_OK)
