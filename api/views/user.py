from rest_framework import generics

from api.models.user import User
from api.serializers.user import UserProfileUpdateSerializer


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user
