from rest_framework import generics

from api.models.project import Project
from api.serializers.project import ProjectSummarySerializer


class ProjectSummaryRetrieveView(generics.RetrieveAPIView):
    queryset = Project.objects.none()
    serializer_class = ProjectSummarySerializer

    def get_object(self):
        return self.request.project
