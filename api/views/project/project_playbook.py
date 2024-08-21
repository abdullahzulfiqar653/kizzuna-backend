from rest_framework import generics
from api.serializers.playbook import PlaybookSerializer


class ProjectPlaybookListCreateView(generics.ListCreateAPIView):
    serializer_class = PlaybookSerializer
    ordering = ["-created_at"]
    search_fields = ["title", "description"]

    def get_queryset(self):
        return self.request.project.playbooks.prefetch_related("takeaways").all()
