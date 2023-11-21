from rest_framework import generics

from takeaway.models import Takeaway
from takeaway.serializers import TakeawaySerializer


class TakeawayRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer

    def get_queryset(self):
        return Takeaway.objects.filter(note__project__users=self.request.user)
