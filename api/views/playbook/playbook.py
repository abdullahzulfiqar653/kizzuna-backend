from django.db import models
from rest_framework import generics

from api.serializers.playbook import PlaybookSerializer


class PlaybookRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlaybookSerializer

    def get_queryset(self):
        return self.request.playbook.project.playbooks.prefetch_related(
            models.Prefetch(
                "notes",
                queryset=self.request.playbook.notes.filter(
                    models.Q(is_shared=True) | models.Q(author=self.request.user),
                ),
            )
        ).all()
