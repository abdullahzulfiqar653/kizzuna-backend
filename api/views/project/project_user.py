from rest_framework import generics

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
        return self.request.project.users.all()
