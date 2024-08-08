from rest_framework import generics
from api.serializers.playbook import PlayBookNoteTakeawaySerializer


class PlaybookTakeawaysListView(generics.ListAPIView):
    serializer_class = PlayBookNoteTakeawaySerializer

    def get_queryset(self):
        return self.request.playbook.notes.all()
