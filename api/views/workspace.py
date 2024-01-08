from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace
from api.serializers.project import ProjectSerializer
from api.serializers.user import UserSerializer
from api.serializers.workspace import WorkspaceSerializer


class WorkspaceUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def list(self, request, pk=None):
        workspace = get_object_or_404(Workspace, pk=pk)

        if not workspace.members.contains(request.user):
            raise PermissionDenied

        members = workspace.members.all()
        serializer = UserSerializer(members, many=True)
        return Response(serializer.data)


class WorkspaceListCreateView(generics.ListCreateAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        return self.request.user.workspaces.all()


class WorkspaceProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        workspace_id = self.kwargs["workspace_id"]
        workspace = user.workspaces.filter(id=workspace_id).first()
        if workspace is None:
            raise PermissionDenied("Do not have permission to access the workspace.")
        return Project.objects.filter(workspace=workspace, users=user).select_related(
            "workspace"
        )
