from rest_framework import generics

from api.models.takeaway_type import TakeawayType
from api.serializers.takeaway_type import TakeawayTypeSerializer


class NoteTakeawayTypeListView(generics.ListAPIView):
    serializer_class = TakeawayTypeSerializer
    queryset = TakeawayType.objects.all()
    ordering = ["-created_at", "name"]
    ordering_fields = ["created_at", "name"]
    search_fields = ["name"]

    def get_queryset(self):
        return TakeawayType.objects.filter(takeaways__note=self.request.note).distinct()
