from rest_framework import exceptions, generics

from api.models.user import User
from api.serializers.user import UserSerializer


class ProjectUserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    ordering = ["last_name"]
    search_fields = [
        "username",
        "first_name",
        "last_name",
    ]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return project.users.all()
