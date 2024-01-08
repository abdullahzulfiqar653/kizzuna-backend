from django.db.models import Count
from rest_framework import exceptions, generics

from api.models.keyword import Keyword
from api.serializers.tag import KeywordSerializer


class ProjectKeywordListView(generics.ListAPIView):
    serializer_class = KeywordSerializer
    queryset = Keyword.objects.all()
    ordering = ["-report_count", "name"]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound
        return (
            Keyword.objects.filter(note__project=project)
            .values("id", "name", "note")
            .values("id", "name")
            .annotate(report_count=Count("*"))
        )
