from rest_framework import generics
from api.serializers.playbook import PlayBookNoteTakeawaysSerializer


class PlaybookTakeawaysListView(generics.ListAPIView):
    serializer_class = PlayBookNoteTakeawaysSerializer

    def get_queryset(self):
        return self.request.playbook.notes.all()
