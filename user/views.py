from django.contrib.auth.models import User as AuthUser
from rest_framework import generics

from .serializers import UserProfileUpdateSerializer


class AuthUserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AuthUser.objects.all()
    serializer_class = UserProfileUpdateSerializer

    def get_object(self):
        return self.request.user
