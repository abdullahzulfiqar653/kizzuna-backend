from rest_framework import exceptions, generics

from tag.models import Tag
from tag.serializers import TagSerializer
from takeaway.models import Insight


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
