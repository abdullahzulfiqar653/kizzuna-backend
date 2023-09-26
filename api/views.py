# api/views.py
from django.contrib.auth.models import User as AuthUser
from django.db.models import Count
from django.utils.module_loading import import_string
from django.views.decorators.debug import sensitive_post_parameters
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_simplejwt.views import TokenObtainPairView, api_settings

from auth.serializers import (AuthUserSerializer, DoPasswordResetSerializer,
                              PasswordUpdateSerializer,
                              RequestPasswordResetSerializer)
from note.models import Note, Project
from note.serializers import NoteSerializer
from project.serializers import ProjectSerializer
from tag.models import Tag
from tag.serializers import TagSerializer
from takeaway.models import Takeaway
from takeaway.serializers import TakeawaySerializer
from user.models import User
from user.serializers import UserSerializer
from workspace.models import Workspace
from workspace.serializers import WorkspaceSerializer


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'notes': reverse('note-list-create', request=request, format=format),
        'projects': reverse('project-list-create', request=request, format=format),
        'workspaces': reverse('workspace-list-create', request=request, format=format),
        'tags': reverse('tag-list-create', request=request, format=format),
        'users': reverse('user-list-create', request=request, format=format),
        'takeaways': reverse('takeaway-list-create', request=request, format=format),
    })

# Signup
class SignupView(generics.CreateAPIView):
    queryset = AuthUser.objects.all()
    serializer_class = AuthUserSerializer
    permission_classes = [AllowAny]
    
    sensitive_post_parameters('password')
    def create(self, request, *args, **kwargs):
        data = request.data

        # Biz logic of signup flow
        auth_user_serializer = AuthUserSerializer(data=data)
        auth_user_serializer.is_valid(raise_exception=True)
        auth_user = auth_user_serializer.save()

        user_serializer = UserSerializer(data=data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        user.auth_user_id = auth_user.id
        user.save()

        # TODO: make this better
        data = request.data.copy()
        if 'workspace_name' in data:
            data['name'] = str(data.pop('workspace_name'))
        workspace_serializer = WorkspaceSerializer(data=data)
        workspace_serializer.is_valid(raise_exception=True)
        workspace = workspace_serializer.save()
        
        workspace.members.add(auth_user)

        headers = self.get_success_headers(auth_user_serializer.data)
        return Response(auth_user_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    
class PasswordUpdateView(generics.CreateAPIView):
    serializer_class = PasswordUpdateSerializer
    
    sensitive_post_parameters('old_password', 'password')
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
    
class RequestPasswordResetView(generics.CreateAPIView):
    serializer_class = RequestPasswordResetSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = RequestPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request=request)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
    
class DoPasswordResetView(generics.CreateAPIView):
    serializer_class = DoPasswordResetSerializer
    permission_classes = [AllowAny]

    sensitive_post_parameters('password')
    def create(self, request, *args, **kwargs):
        serializer = DoPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(request=request)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)
    
# Token
class TokenObtainPairAndRefreshView(TokenObtainPairView):
    def get_serializer_class(self):
        match self.request.data.get('grant_type'):
            case 'password' | None: 
                return import_string(api_settings.TOKEN_OBTAIN_SERIALIZER)
            case 'refresh_token':
                return import_string(api_settings.TOKEN_REFRESH_SERIALIZER)

# TODO: shift to tag views
# Tag
class TagListCreateView(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class TagRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

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

# TODO: shift to project views
# Project
class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_queryset(self):
        auth_user = self.request.user
        workspace = auth_user.workspaces.first()
        return Project.objects.filter(workspace=workspace, users=auth_user)
    
    def create(self, request, *args, **kwargs):
        auth_user = self.request.user
        workspace = auth_user.workspaces.first()
        if workspace.projects.count() > 1:
            # We restrict user from creating more than 2 projects per workspace
            raise PermissionDenied('Cannot create more than 2 projects in one workspace.')
        return super().create(request, *args, **kwargs)

class ProjectRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

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

# TODO: shift to note views
# Note
class NoteListCreateView(generics.ListCreateAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    def get_queryset(self):
        return (
            super().get_queryset()
            .annotate(takeaway_count=Count('takeaways'))
            .annotate(participant_count=Count('user_participants'))
        )

class NoteRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    
    def get_queryset(self):
        return (
            super().get_queryset()
            .annotate(takeaway_count=Count('takeaways'))
            .annotate(participant_count=Count('user_participants'))
        )

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

# TODO: shift to takeaway views
# Takeaway
class TakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer

class TakeawayRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer

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
