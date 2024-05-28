# api/views.py

from django.utils.module_loading import import_string
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView, api_settings

from api.models.invitation import Invitation
from api.models.user import User
from api.serializers.auth import (
    DoPasswordResetSerializer,
    GoogleLoginSerializer,
    InvitationSignupSerializer,
    InvitationStatusSerializer,
    PasswordUpdateSerializer,
    RequestPasswordResetSerializer,
    SignupSerializer,
)


# Signup
class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        request._request.sensitive_post_parameters = ("password",)
        return super().create(request, *args, **kwargs)


class GoogleLoginView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = GoogleLoginSerializer

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PasswordUpdateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordUpdateSerializer

    def create(self, request, *args, **kwargs):
        request._request.sensitive_post_parameters = ("old_password", "password")
        return super().create(request, *args, **kwargs)


class RequestPasswordResetView(generics.CreateAPIView):
    serializer_class = RequestPasswordResetSerializer
    permission_classes = [AllowAny]


class DoPasswordResetView(generics.CreateAPIView):
    serializer_class = DoPasswordResetSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        request._request.sensitive_post_parameters = ("password",)
        return super().create(request, *args, **kwargs)


# Token
class TokenObtainPairAndRefreshView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        match self.request.data.get("grant_type"):
            case "password" | None:
                return import_string(api_settings.TOKEN_OBTAIN_SERIALIZER)
            case "refresh_token":
                return import_string(api_settings.TOKEN_REFRESH_SERIALIZER)


class InvitationStatusRetrieveView(generics.RetrieveAPIView):
    serializer_class = InvitationStatusSerializer
    permission_classes = [AllowAny]
    lookup_field = "token"
    queryset = Invitation.objects.all()


class InvitationSignupCreateView(generics.CreateAPIView):
    serializer_class = InvitationSignupSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        request._request.sensitive_post_parameters = ("password",)
        return super().create(request, *args, **kwargs)
