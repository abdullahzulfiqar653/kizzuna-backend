from django.contrib.auth.models import update_last_login
from googleapiclient.discovery import build
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from api.integrations.google import google_flow as google_normal_flow
from api.integrations.google import google_verification_flow
from api.models.integrations.google.calendar.channel import GoogleCalendarChannel
from api.models.integrations.google.credential import GoogleCredential
from api.models.user import User
from api.serializers.auth import create_mixpanel_user
from api.tasks import sync_google_calendar_channel


class GoogleAuthCallbackSerializer(serializers.Serializer):
    code = serializers.CharField(write_only=True)
    google = serializers.BooleanField(write_only=True, default=False)
    access_token = serializers.CharField(read_only=True)
    refresh_token = serializers.CharField(read_only=True)

    def validate(self, data):
        code = data.get("code")
        is_google = data.get("google", False)
        try:
            if is_google:
                # TODO: Remove this after verifying the flow
                google_flow = google_verification_flow
            else:
                google_flow = google_normal_flow
            google_flow.fetch_token(code=code)
        except Exception as e:
            print(e)
            raise serializers.ValidationError({"code": "Authentication failed."})
        creds = google_flow.credentials
        data["creds"] = creds
        return data

    def save(self, **kwargs):
        creds = self.validated_data["creds"]
        userinfo = self.get_userinfo(creds)
        user, created = self.get_or_create_user(userinfo)

        credential, created = GoogleCredential.update_or_create(user, creds)
        if not credential.calendar_channels.exists():
            channel = GoogleCalendarChannel.create(credential)
            sync_google_calendar_channel.delay(channel.id)

        # Generate access and refresh token
        refresh = RefreshToken.for_user(user)
        self.validated_data.update(
            {
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }
        )
        update_last_login(None, user)

    def get_userinfo(self, creds):
        service = build("oauth2", "v2", credentials=creds)
        return service.userinfo().get().execute()

    def get_or_create_user(self, userinfo):
        user, created = User.objects.get_or_create(
            username__iexact=userinfo.get("email").lower(),
            defaults={
                "username": userinfo.get("email").lower(),
                "first_name": userinfo.get("given_name"),
                "last_name": userinfo.get("family_name"),
                "email": userinfo.get("email"),
            },
        )
        if created:
            user.set_unusable_password()
            user.save()
            create_mixpanel_user(user)
        return user, created
