
from rest_framework import exceptions, generics

from project.models import Project
from project.serializers import ProjectSerializer


class ProjectRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return self.request.user.projects.select_related('workspace').all()
