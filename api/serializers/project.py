# api/serializers.py
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from api.models.project import Project
from api.serializers.workspace import WorkspaceSerializer, WorkspaceUsageSerializer


class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    workspace = WorkspaceSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "workspace", "language"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        view = self.context.get("view")
        workspace_id = view.kwargs.get("workspace_id")

        workspace = user.workspaces.filter(id=workspace_id).first()
        if workspace is None:
            raise PermissionDenied("Do not have permission to access the workspace.")

        if workspace.projects.count() > 1:
            # We restrict user from creating more than 2 projects per workspace
            raise PermissionDenied("Hit project limit of the workspace.")

        validated_data["workspace"] = workspace
        validated_data["users"] = [user]
        return super().create(validated_data)


class ProjectUsageSerializer(ProjectSerializer):
    workspace = WorkspaceUsageSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ["id", "name", "description", "workspace", "language"]
