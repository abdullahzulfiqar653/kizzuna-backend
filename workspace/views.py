from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from user.serializers import UserSerializer

from .forms import WorkspaceForm
from .models import Workspace
from .serializers import WorkspaceSerializer


def workspace_list(request):
    workspaces = Workspace.objects.all()
    return render(request, 'workspace_list.html', {'workspaces': workspaces})

def workspace_detail(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    return render(request, 'workspace_detail.html', {'workspace': workspace})

def workspace_create(request):
    if request.method == 'POST':
        form = WorkspaceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('workspace-list')
    else:
        form = WorkspaceForm()
    return render(request, 'workspace_form.html', {'form': form})

def workspace_update(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    if request.method == 'POST':
        form = WorkspaceForm(request.POST, instance=workspace)
        if form.is_valid():
            form.save()
            return redirect('workspace-list')
    else:
        form = WorkspaceForm(instance=workspace)
    return render(request, 'workspace_form.html', {'form': form})

def workspace_delete(request, workspace_id):
    workspace = get_object_or_404(Workspace, id=workspace_id)
    if request.method == 'POST':
        workspace.delete()
        return redirect('workspace-list')
    return render(request, 'workspace_confirm_delete.html', {'workspace': workspace})


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


class WorkspaceRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)