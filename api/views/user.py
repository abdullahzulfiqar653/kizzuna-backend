from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from api.models.user import User
from api.serializers.user_profile import UserProfileUpdateSerializer


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user
