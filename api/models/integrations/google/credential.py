from django.conf import settings
from django.db import models
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from api.models.user import User


class GoogleCredential(models.Model):
    # NOTE: We use credential (singular) to indicate the django model object,
    # and creds to indicate google auth Credentials object
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="google_credential",
    )
    token = models.TextField()
    refresh_token = models.TextField()
    token_uri = models.URLField()
    client_id = models.TextField()
    client_secret = models.TextField()
    scopes = models.JSONField()
    expiry = models.DateTimeField()

    @classmethod
    def create(cls, user: User, creds: Credentials):
        return cls.objects.create(
            user=user,
            token=creds.token,
            refresh_token=creds.refresh_token,
            token_uri=creds.token_uri,
            client_id=creds.client_id,
            client_secret=creds.client_secret,
            scopes=creds.scopes,
            expiry=creds.expiry.astimezone(),
        )

    @classmethod
    def update_or_create(cls, user: User, creds: Credentials):
        return cls.objects.update_or_create(
            user=user,
            defaults={
                "token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
                "expiry": creds.expiry.astimezone(),
            },
        )

    def to_credentials(self) -> Credentials:
        return Credentials(
            token=self.token,
            refresh_token=self.refresh_token,
            token_uri=self.token_uri,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes,
            expiry=self.expiry.replace(tzinfo=None),
        )

    def refresh(self):
        creds = self.to_credentials()
        creds.refresh(Request())
        self, created = self.update_or_create(user=self.user, creds=creds)
        return self

    def get_userinfo(self):
        creds = self.to_credentials()
        service = build("oauth2", "v2", credentials=creds)
        return service.userinfo().get().execute()
