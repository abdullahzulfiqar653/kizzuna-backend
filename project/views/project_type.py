from django.db.models import F
from rest_framework import exceptions, generics

from note.models import Note
from note.serializers import NameOnlySerializer


class ProjectTypeListView(generics.ListAPIView):
    serializer_class = NameOnlySerializer
    queryset = Note.objects.all()
    ordering = ["name"]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return (
            Note.objects.filter(project=project)
            .annotate(name=F("type"))
            .values("name")
            .distinct()
        )
