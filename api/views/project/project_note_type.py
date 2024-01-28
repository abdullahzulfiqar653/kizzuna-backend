from django.db.models import Count, F
from rest_framework import generics

from api.models.note import Note
from api.serializers.note import ProjectNoteTypeSerializer


class ProjectNoteTypeListView(generics.ListAPIView):
    serializer_class = ProjectNoteTypeSerializer
    queryset = Note.objects.all()
    ordering = ["-report_count", "name"]
    search_fields = ["name"]

    def get_queryset(self):
        return (
            Note.objects.filter(project=self.request.project)
            .annotate(name=F("type"))
            .values("name")
            .annotate(report_count=Count("*"))
        )
