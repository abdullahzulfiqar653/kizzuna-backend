import requests
from django.conf import settings
from rest_framework import serializers

from api.models.integrations.googledrive.credential import GoogleDriveCredential
from api.models.integrations.googledrive.oauth_state import GoogleDriveOAuthState


class GoogleDriveOauthUrlSerializer(serializers.Serializer):
    redirect_uri = serializers.URLField(read_only=True)


class GoogleDriveOauthRedirectSerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
    state = serializers.CharField(required=True)

    def validate(self, data):
        code = data.get("code")
        state = data.get("state")

        oauth_state = GoogleDriveOAuthState.objects.filter(state=state).first()
        if not oauth_state:
            raise serializers.ValidationError({"state": "Invalid state parameter."})

        token_request_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        response = requests.post(
            "https://oauth2.googleapis.com/token", data=token_request_data
        )
        response_data = response.json()

        if "access_token" not in response_data:
            raise serializers.ValidationError({"google": "Authentication failed."})

        data["response"] = response_data
        return data

    def save(self, **kwargs):

        data = self.validated_data
        response_data = data["response"]
        user = self.context["request"].user
        project = self.context["request"].project

        if "refresh_token" not in response_data:
            try:
                existing_user = GoogleDriveCredential.objects.get(
                    user=user, project=project
                )
                refresh_token = existing_user.refresh_token
            except GoogleDriveCredential.DoesNotExist:
                raise serializers.ValidationError(
                    "No refresh token found and not provided by Google"
                )
        else:
            refresh_token = response_data["refresh_token"]

        GoogleDriveCredential.objects.update_or_create(
            user=user,
            project=project,
            defaults={
                "access_token": response_data["access_token"],
                "refresh_token": refresh_token,
                "token_type": response_data["token_type"],
                "expires_in": response_data["expires_in"],
            },
        )

        oauth_state = GoogleDriveOAuthState.objects.get(state=data.get("state"))
        oauth_state.delete()
