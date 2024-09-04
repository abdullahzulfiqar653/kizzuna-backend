from django.db import models
from rest_framework import generics

from api.models.playbook_takeaway import PlaybookTakeaway
from api.serializers.playbook_takeaway import PlaybookTakeawaySerializer


class PlaybookVideoTakeawaysListCreateView(generics.ListCreateAPIView):
    queryset = PlaybookTakeaway.objects.none()
    serializer_class = PlaybookTakeawaySerializer
    ordering = ["order"]

    def get_queryset(self):
        return self.request.playbook.playbook_takeaways.filter(
            models.Q(takeaway__note__is_shared=True)
            | models.Q(takeaway__note__author=self.request.user)
        ).all()


class PlaybookVideoTakeawaysUpdateDestroyView(
    generics.DestroyAPIView, generics.UpdateAPIView
):
    serializer_class = PlaybookTakeawaySerializer
    lookup_field = "takeaway_id"

    def get_queryset(self):
        return self.request.playbook.playbook_takeaways.filter(
            models.Q(takeaway__note__is_shared=True)
            | models.Q(takeaway__note__author=self.request.user)
        ).all()

    def perform_destroy(self, instance: PlaybookTakeaway):
        super().perform_destroy(instance)
        instance.playbook.update_playbook_takeaway_times()
        instance.playbook.create_playbook_clip_and_thumbnail()
