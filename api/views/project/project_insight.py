from django.db.models import Count
from rest_framework import generics

from api.models.insight import Insight
from api.serializers.insight import ProjectInsightSerializer


class ProjectInsightListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectInsightSerializer
    queryset = Insight.objects.all()
    ordering_fields = [
        "created_at",
        "takeaway_count",
        "created_by__first_name",
        "created_by__last_name",
        "title",
    ]
    search_fields = [
        "title",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.request.project.insights.annotate(takeaway_count=Count("takeaways"))
