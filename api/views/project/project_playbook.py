from django.db import models
from django.db.models import Prefetch
from rest_framework import generics

from api.models.playbook import Playbook
from api.serializers.playbook import PlaybookSerializer


class ProjectPlaybookListCreateView(generics.ListCreateAPIView):
    serializer_class = PlaybookSerializer
    queryset = Playbook.objects.none()
    ordering = ["-created_at"]
    search_fields = ["title", "description"]

    def get_queryset(self):
        return self.request.project.playbooks.prefetch_related(
            Prefetch(
                "notes",
                queryset=self.request.project.notes.filter(
                    models.Q(is_shared=True) | models.Q(author=self.request.user),
                ),
            )
        ).all()
