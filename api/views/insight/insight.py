from rest_framework import generics

from api.models.insight import Insight
from api.serializers.takeaway import InsightSerializer


class InsightRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Insight.objects.all()
    serializer_class = InsightSerializer

    def get_queryset(self):
        return Insight.objects.filter(project__users=self.request.user)
