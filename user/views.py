from django.contrib.auth.models import User as AuthUser
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import generics, status
from rest_framework.response import Response

from project.models import Project
from project.serializers import ProjectSerializer
from workspace.models import Workspace
from workspace.serializers import WorkspaceSerializer

from .forms import UserForm
from .models import User
from .serializers import UserProfileUpdateSerializer, UserSerializer


# TODO: DELETE START
def user_list(request):
    users = User.objects.all()
    return render(request, 'user_list.html', {'users': users})

def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return render(request, 'user_detail.html', {'user': user})

def user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user-list')
    else:
        form = UserForm()
    return render(request, 'user_form.html', {'form': form})

def user_update(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-list')
    else:
        form = UserForm(instance=user)
    return render(request, 'user_form.html', {'form': form})

def user_delete(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('user-list')
    return render(request, 'user_confirm_delete.html', {'user': user})

# TODO: DELETE END


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
    
class AuthUserRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = AuthUser.objects.all()
    serializer_class = UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user

class AuthUserWorkspaceListView(generics.ListAPIView):
    serializer_class = WorkspaceSerializer

    def list(self, request, auth_user_id):
        auth_user = get_object_or_404(AuthUser, id=auth_user_id)
       
        # TODO: Check permission
        # if not workspace.members.contains(request.user):
        #     PermissionDenied

        workspace = (
            Workspace.objects.filter(members=auth_user)
            # .filter(member=request.user)
        )
        serializer = WorkspaceSerializer(workspace, many=True)
        return Response(serializer.data)
    
class AuthUserProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer

    def list(self, request, auth_user_id):
        auth_user = get_object_or_404(AuthUser, id=auth_user_id)

        project = (
            Project.objects.filter(users=auth_user)
            # .filter(users=request.user)
        )
        serializer = ProjectSerializer(project, many=True)
        return Response(serializer.data)