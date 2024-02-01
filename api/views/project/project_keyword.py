from django.db.models import Count
from rest_framework import generics

from api.models.keyword import Keyword
from api.serializers.tag import KeywordSerializer


class ProjectKeywordListView(generics.ListAPIView):
    serializer_class = KeywordSerializer
    queryset = Keyword.objects.all()
    ordering = ["-report_count", "name"]

    def get_queryset(self):
        return (
            Keyword.objects.filter(notes__project=self.request.project)
            .values("id", "name", "notes")
            .values("id", "name")
            .annotate(report_count=Count("*"))
        )
