from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from rest_framework import exceptions, generics

from api.serializers.integrations.googledrive.googledrive_files import (
    GoogleDriveFileSerializer,
)


class GoogleDriveListFilesView(generics.ListAPIView):
    serializer_class = GoogleDriveFileSerializer
    filter_backends = []

    def get_queryset(self):
        if not hasattr(self.request.user, "google_credential"):
            raise exceptions.ValidationError("Google Drive account not connected")
        creds = self.request.user.google_credential.to_credentials()
        drive_service = build("drive", "v3", credentials=creds)
        try:
            results = drive_service.files().list().execute()
        except HttpError as e:
            raise exceptions.ValidationError(
                "Failed to retrieve files from Google Drive"
            )
        return results.get("files", [])
