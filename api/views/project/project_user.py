from django.db import models
from rest_framework import generics

from api.models.user import User
from api.models.workspace_user import WorkspaceUser
from api.serializers.user import ProjectUserListSerializer


class ProjectUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = ProjectUserListSerializer
    ordering = ["last_name"]
    search_fields = [
        "username",
        "first_name",
        "last_name",
    ]

    def get_queryset(self):
        workspace_users = WorkspaceUser.objects.filter(
            workspace=self.request.project.workspace, user=models.OuterRef("pk")
        )
        return self.request.project.users.annotate(
            role=models.Subquery(workspace_users.values("role")[:1]),
        )
