from rest_framework import generics
from api.serializers.playbook_takeaway import PlaybookTakeawaySerializer


class PlaybookVideoTakeawaysListCreateView(generics.ListCreateAPIView):
    serializer_class = PlaybookTakeawaySerializer

    def get_queryset(self):
        return self.request.playbook.playbook_takeaways.all()


class PlaybookVideoTakeawaysUpdateDestroyView(
    generics.DestroyAPIView, generics.UpdateAPIView
):
    serializer_class = PlaybookTakeawaySerializer
    lookup_field = "takeaway_id"

    def get_queryset(self):
        return self.request.playbook.playbook_takeaways.all()
