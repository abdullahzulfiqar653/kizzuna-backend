from django.db.models import Count, F
from rest_framework import generics

from api.models.note import Note
from api.serializers.note import ProjectSentimentSerializer


class ProjectSentimentListView(generics.ListAPIView):
    serializer_class = ProjectSentimentSerializer
    queryset = Note.objects.all()
    ordering = ["-report_count"]
    search_fields = ["name"]

    def get_queryset(self):
        return (
            Note.objects.filter(project=self.request.project)
            .annotate(name=F("sentiment"))
            .values("name")
            .annotate(report_count=Count("*"))
        )
