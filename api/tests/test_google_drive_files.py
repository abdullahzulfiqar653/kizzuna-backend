import json
import logging
import secrets
from unittest.mock import MagicMock, patch

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.integrations.google.credential import GoogleCredential
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class GoogleDriveFilesViewTests(APITestCase):
    def setUp(self):
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)
        logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_authenticate(user=self.user)
        self.workspace = Workspace.objects.create(
            name="Test Workspace", owned_by=self.user
        )
        self.project = Project.objects.create(
            id="test_project", name="Test Project", workspace=self.workspace
        )
        self.project.users.add(self.user)
        self.list_files_url = (
            f"/api/projects/{self.project.id}/integrations/google_drive/files/"
        )

    @patch("httplib2.Http.request")
    def test_list_files_success(self, mock_request):
        GoogleCredential.objects.create(
            user=self.user,
            token=secrets.token_hex(32),
            refresh_token=secrets.token_hex(32),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=secrets.token_hex(32),
            client_secret=secrets.token_hex(32),
            scopes=["https://www.googleapis.com/auth/drive"],
            expiry=timezone.now() + timezone.timedelta(hours=1),
        )

        mock_request.side_effect = [
            (
                MagicMock(status=200),
                json.dumps(
                    {
                        "files": [
                            {"id": "file1", "name": "File 1", "mimeType": "text/plain"},
                            {"id": "file2", "name": "File 2", "mimeType": "image/png"},
                        ]
                    }
                ).encode(),
            )
        ]

        response = self.client.get(self.list_files_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["name"], "File 1")
        self.assertEqual(response.data[1]["mimeType"], "image/png")

    def test_list_files_no_google_drive_user(self):
        GoogleCredential.objects.all().delete()
        response = self.client.get(self.list_files_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Google Drive account not connected", str(response.data))

    @patch("httplib2.Http.request")
    def test_list_files_failed_to_retrieve_files(self, mock_request):
        GoogleCredential.objects.create(
            user=self.user,
            token=secrets.token_hex(32),
            refresh_token=secrets.token_hex(32),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=secrets.token_hex(32),
            client_secret=secrets.token_hex(32),
            scopes=["https://www.googleapis.com/auth/drive"],
            expiry=timezone.now() + timezone.timedelta(hours=1),
        )

        mock_request.side_effect = [
            (
                MagicMock(status=500),
                json.dumps({"error": "Internal Server Error"}).encode(),
            ),
        ]

        response = self.client.get(self.list_files_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Failed to retrieve files from Google Drive", str(response.data))
