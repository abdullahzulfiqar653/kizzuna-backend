from rest_framework import generics

from api.models.playbook_takeaway import PlaybookTakeaway
from api.serializers.playbook_takeaway import PlaybookTakeawaySerializer


class PlaybookVideoTakeawaysListCreateView(generics.ListCreateAPIView):
    queryset = PlaybookTakeaway.objects.none()
    serializer_class = PlaybookTakeawaySerializer
    ordering = ["order"]

    def get_queryset(self):
        return self.request.playbook.playbook_takeaways.all()


class PlaybookVideoTakeawaysUpdateDestroyView(
    generics.DestroyAPIView, generics.UpdateAPIView
):
    serializer_class = PlaybookTakeawaySerializer
    lookup_field = "takeaway_id"

    def get_queryset(self):
        return self.request.playbook.playbook_takeaways.all()

    def perform_destroy(self, instance: PlaybookTakeaway):
        super().perform_destroy(instance)
        instance.playbook.update_playbook_takeaway_times()
        instance.playbook.create_playbook_clip_and_thumbnail()
