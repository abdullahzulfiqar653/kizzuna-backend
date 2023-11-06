
from rest_framework import exceptions, generics

from user.serializers import AuthUserSerializer


class ProjectAuthUserListView(generics.ListAPIView):
    serializer_class = AuthUserSerializer
    ordering = ['last_name']
    search_fields = [
        'username',
        'first_name',
        'last_name',
    ]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return project.users.all()
