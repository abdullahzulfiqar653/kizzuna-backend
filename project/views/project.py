
from rest_framework import exceptions, generics

from project.models import Project
from project.serializers import ProjectSerializer


class ProjectListCreateView(generics.ListCreateAPIView):
    # TODO: To be deprecated and replaced WorkspaceProjectListCreateView
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    ordering = ['-created_at']

    def get_queryset(self):
        auth_user = self.request.user
        workspace = auth_user.workspaces.first()
        return Project.objects.filter(workspace=workspace, users=auth_user)

    def create(self, request, *args, **kwargs):
        auth_user = self.request.user
        workspace = auth_user.workspaces.first()
        if workspace.projects.count() > 1:
            # We restrict user from creating more than 2 projects per workspace
            raise exceptions.PermissionDenied('Cannot create more than 2 projects in one workspace.')
        return super().create(request, *args, **kwargs)


class ProjectRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return self.request.user.projects.all()
