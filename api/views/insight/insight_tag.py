from rest_framework import exceptions, generics

from api.models.insight import Insight
from api.models.tag import Tag
from api.serializers.tag import TagSerializer


class InsightTagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    ordering = ["name"]

    def get_queryset(self):
        insight_id = self.kwargs["insight_id"]
        insight = Insight.objects.filter(
            id=insight_id, project__users=self.request.user
        ).first()
        if insight is None:
            raise exceptions.NotFound("Insight not found.")

        return Tag.objects.filter(takeaways__insights=insight)
