# api/serializers.py
from django.core.exceptions import PermissionDenied
from rest_framework import serializers

from project.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'status']

    def __init__(self, *args, **kwargs):
        request = kwargs.get('context', {}).get('request')
        if request is not None and hasattr(request, 'user'):
            self.user = request.user
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        request = self.context.get('request')
        auth_user = request.user
        view = self.context.get('view')
        workspace_id = view.kwargs.get('workspace_id')

        # TODO: Once frontend supply the workspace_id, remove the if, keep the else
        if workspace_id is None:
            workspace = auth_user.workspaces.first()
        else:
            workspace = auth_user.workspaces.filter(id=workspace_id).first()
            if workspace is None:
                raise PermissionDenied('Do not have permission to access the workspace.')

        if workspace.projects.count() > 1:
            # We restrict user from creating more than 2 projects per workspace
            raise PermissionDenied('Hit project limit of the workspace.')

        validated_data['workspace'] = workspace
        validated_data['users'] = [auth_user]
        return super().create(validated_data)
