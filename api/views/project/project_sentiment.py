from django.db.models import Count, F
from rest_framework import exceptions, generics

from api.models.note import Note
from api.serializers.note import ProjectSentimentSerializer


class ProjectSentimentListView(generics.ListAPIView):
    serializer_class = ProjectSentimentSerializer
    queryset = Note.objects.all()
    ordering = ["-report_count"]
    search_fields = ["name"]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return (
            Note.objects.filter(project=project)
            .annotate(name=F("sentiment"))
            .values("name")
            .annotate(report_count=Count("*"))
        )
