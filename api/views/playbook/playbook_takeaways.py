from rest_framework import generics
from api.filters.takeaway import NoteTakeawayFilter
from api.serializers.playbook import PlayBookNoteTakeawaySerializer


class PlaybookTakeawaysListView(generics.ListAPIView):
    serializer_class = PlayBookNoteTakeawaySerializer
    filterset_class = NoteTakeawayFilter

    def get_queryset(self):
        return self.request.playbook.notes.all()
