from rest_framework import generics, permissions

from api.serializers.integrations.google.auth.callback import (
    GoogleAuthCallbackSerializer,
)


class GoogleAuthCallbackCreateView(generics.CreateAPIView):
    serializer_class = GoogleAuthCallbackSerializer
    permission_classes = [permissions.AllowAny]
