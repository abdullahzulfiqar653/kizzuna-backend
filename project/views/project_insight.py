from django.db.models import Count
from rest_framework import generics

from takeaway.models import Insight
from takeaway.serializers import ProjectInsightSerializer


class ProjectInsightListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectInsightSerializer
    queryset = Insight.objects.all()
    ordering_fields = [
        'created_at',
        'takeaway_count',
        'created_by__first_name',
        'created_by__last_name',
        'title',
    ]
    search_fields = [
        'title',
        'created_by__username',
        'created_by__first_name',
        'created_by__last_name',
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        return (
            Insight.objects
            .annotate(takeaway_count=Count('takeaways'))
            .filter(project__users=self.request.user)
        )
