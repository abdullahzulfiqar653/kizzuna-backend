from rest_framework import generics
from api.serializers.playbook import PlayBookSerializer


class ProjectPlayBookListCreateView(generics.ListCreateAPIView):
    serializer_class = PlayBookSerializer
    ordering = ["-created_at"]

    def get_queryset(self):
        return self.request.project.workspace.playbooks.all()
