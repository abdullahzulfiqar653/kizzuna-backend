from rest_framework import generics
from api.serializers.takeaway import TakeawaySerializer



class PlaybookVideoTakeawaysListView(generics.ListAPIView):
    serializer_class = TakeawaySerializer

    def get_queryset(self):
        return self.request.playbook.highlights.all()
