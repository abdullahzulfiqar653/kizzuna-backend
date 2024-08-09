import logging
from unittest.mock import MagicMock, patch

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.integrations.googledrive.credential import GoogleDriveCredential
from api.models.integrations.googledrive.oauth_state import GoogleDriveOAuthState
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class GoogleDriveOAuthTests(APITestCase):
    def setUp(self):
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client.force_authenticate(user=self.user)

        self.workspace = Workspace.objects.create(
            name="Test Workspace", owned_by=self.user
        )

        self.project = Project.objects.create(
            id="test_project", name="Test Project", workspace=self.workspace
        )
        self.project.users.add(self.user)

        self.project_id = self.project.id
        self.oauth_start_url = (
            f"/api/projects/{self.project_id}/integrations/google_drive/oauth-url/"
        )
        self.oauth_callback_url = (
            f"/api/projects/{self.project_id}/integrations/google_drive/oauth-redirect/"
        )

    @patch(
        "api.models.integrations.googledrive.oauth_state.GoogleDriveOAuthState.save",
        MagicMock(),
    )
    def test_oauth_start_creates_state(self):
        response = self.client.get(self.oauth_start_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("redirect_uri", response.data)

    @patch("requests.post")
    def test_oauth_callback_validates_state(self, mock_post):
        mock_post.return_value.json.return_value = {
            "access_token": "some_access_token",
            "refresh_token": "some_refresh_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        # Create a valid state in the database for testing
        valid_state = GoogleDriveOAuthState.objects.create(
            user=self.user, state="valid_state123"
        )

        # Test callback with valid state
        response = self.client.post(
            self.oauth_callback_url, {"code": "12345", "state": valid_state.state}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(
            GoogleDriveOAuthState.objects.filter(state="valid_state123").exists()
        )

        # Check if GoogleDriveUser is created
        self.assertTrue(GoogleDriveCredential.objects.filter(user=self.user).exists())

        # Test callback with invalid state
        response = self.client.post(
            self.oauth_callback_url, {"code": "12345", "state": "invalid_state123"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("requests.post")
    def test_oauth_callback_handles_no_refresh_token(self, mock_post):
        mock_post.return_value.json.return_value = {
            "access_token": "some_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }

        # Create a valid state in the database for testing
        valid_state = GoogleDriveOAuthState.objects.create(
            user=self.user, state="valid_state123"
        )

        # Ensure GoogleDriveUser does not exist initially
        GoogleDriveCredential.objects.filter(user=self.user).delete()

        # Test callback with no refresh token and no existing user
        response = self.client.post(
            self.oauth_callback_url, {"code": "12345", "state": valid_state.state}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
