from rest_framework import generics

from api.models.tag import Tag
from api.serializers.tag import TagSerializer


class NoteTagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    ordering = ["-takeaway_count", "name"]
    ordering_fields = ["created_at", "takeway_count", "name"]

    def get_queryset(self):
        return Tag.objects.filter(takeaways__note=self.request.note).distinct()