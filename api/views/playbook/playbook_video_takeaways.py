from rest_framework import generics, status, exceptions
from rest_framework.response import Response
from api.serializers.playbook_takeaway import PlaybookTakeawaySerializer
from api.models.takeaway import Takeaway


class PlaybookVideoTakeawaysListCreateView(generics.ListCreateAPIView):
    serializer_class = PlaybookTakeawaySerializer

    def get_queryset(self):
        return self.request.playbook.takeaways.all()


class PlaybookVideoTakeawaysUpdateDestroyView(
    generics.DestroyAPIView, generics.UpdateAPIView
):
    serializer_class = PlaybookTakeawaySerializer
    lookup_field = "takeaway_id"

    def get_queryset(self):
        return self.request.playbook.takeaways.all()

    def get_object(self):
        takeaway_id = self.kwargs.get("takeaway_id")
        try:
            return self.get_queryset().get(pk=takeaway_id)
        except Takeaway.DoesNotExist:
            raise exceptions.NotFound(f"Takeaway {takeaway_id} not found")

    def destroy(self, request, playbook_id, takeaway_id):
        try:
            takeaway = self.get_queryset().get(pk=takeaway_id)
        except Takeaway.DoesNotExist:
            raise exceptions.NotFound(f"Takeaway {takeaway_id} not found")

        self.request.playbook.takeaways.remove(takeaway)
        return Response(status=status.HTTP_204_NO_CONTENT)
