from rest_framework import exceptions, generics

from tag.models import Keyword
from tag.serializers import KeywordSerializer


class ProjectKeywordListView(generics.ListAPIView):
    serializer_class = KeywordSerializer
    queryset = Keyword.objects.all()
    ordering = ["name"]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound
        return Keyword.objects.filter(note__project=project).distinct()
