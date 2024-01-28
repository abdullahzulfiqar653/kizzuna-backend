from rest_framework import generics

from api.models.tag import Tag
from api.serializers.tag import TagSerializer


class InsightTagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    ordering = ["name"]

    def get_queryset(self):
        return Tag.objects.filter(takeaways__insights=self.request.insight).distinct()
