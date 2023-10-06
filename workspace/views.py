from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from user.serializers import UserSerializer

from .models import Workspace
from .serializers import WorkspaceSerializer


class WorkspaceUserListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def list(self, request, pk=None):
        workspace = get_object_or_404(Workspace, pk=pk)
       
        # TODO: Check permission
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
