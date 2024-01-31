from rest_framework import generics

from api.models.insight import Insight
from api.serializers.insight import InsightSerializer


class InsightRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Insight.objects.all()
    serializer_class = InsightSerializer
