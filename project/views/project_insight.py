from django.db.models import Count
from rest_framework import generics

from takeaway.models import Insight
from takeaway.serializers import ProjectInsightSerializer


class ProjectInsightListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectInsightSerializer

    def get_queryset(self):
        return (
            Insight.objects
            .annotate(takeaway_count=Count('takeaways'))
            .filter(project__users=self.request.user)
        )
