import logging
from unittest.mock import patch

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.invitation import Invitation
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestNoteKeywordDestroyView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.existing_user = User.objects.create_user(
            username="USER@example.com",
            password="password",
            email="USER@example.com",
        )

        self.workspace = Workspace.objects.create(
            name="workspace", owned_by=self.existing_user
        )
        self.workspace.members.add(
            self.existing_user, through_defaults={"role": "Editor"}
        )
        self.project = Project.objects.create(name="project", workspace=self.workspace)
        self.project.users.add(self.existing_user)

    def test_token_obtain_pair_case_insensitive(self):
        """
        Make sure to validate with lowercase username even though
        existing username contains uppercase
        """
        url = "/api/token/"
        response = self.client.post(
            url, {"username": "user@example.com", "password": "password"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("requests.get")
    def test_google_login_case_insensitive(self, mocked_get):
        """
        Check the google sign in endpoint can detect user case insensitively
        """

        class Response:
            status_code = status.HTTP_200_OK

            def json(self):
                return {"email": "user@example.com"}

        mocked_get.return_value = Response()

        url = "/api/token/google/"
        data = {"google_access_token": "token"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mocked_get.assert_called_once_with(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer token"},
        )

        # Check that no new user is created
        bot = User.objects.get(username="bot@raijin.ai")
        self.assertCountEqual(User.objects.all(), [bot, self.existing_user])

    @patch("requests.get")
    def test_google_signup_with_uppercase_username(self, mocked_get):
        """
        Check the google sign up results in lowercase username
        """

        class Response:
            status_code = status.HTTP_200_OK

            def json(self):
                return {
                    "email": "UPPERCASE_USER@example.com",
                    "given_name": "user_first_name",
                    "family_name": "user_last_name",
                }

        mocked_get.return_value = Response()

        url = "/api/token/google/"
        data = {"google_access_token": "token"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        mocked_get.assert_called_once_with(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer token"},
        )

        # Make sure that the created username is lowercase
        newly_created_user = User.objects.latest("date_joined")
        self.assertEqual(newly_created_user.username, "uppercase_user@example.com")

    def test_invite_status_case_insensitive(self):
        """
        Make sure to detect user case insenitively when signing up users
        """
        # Create an invitation
        invitation = Invitation.objects.create(
            sender=self.existing_user,
            recipient_email="user@example.com",
            token="token",
            workspace=self.workspace,
            project=self.project,
            expires_at=timezone.now() + timezone.timedelta(days=1),
        )

        # Check invitation status responds correctly
        url = f"/api/invitation/{invitation.token}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.json(),
            {
                "detail": [
                    "The email user@example.com has already been taken. "
                    "If you are the account owner, "
                    "please login and click on the invitation link again."
                ]
            },
        )

        # Check that users cannot signup a new account
        url = "/api/invitation/signup/"
        data = {
            "first_name": "user_first_name",
            "last_name": "user_last_name",
            "password": "super_complicated_password",
            "token": invitation.token,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            response.json(),
            {"detail": ["Email user@example.com has already been taken."]},
        )

    def test_invite_user_signup_with_uppercase_username(self):
        """
        Make sure that the invitation signup results in lowercase username
        """
        # Create an invitation
        invitation = Invitation.objects.create(
            sender=self.existing_user,
            recipient_email="UPPERCASE_USER@example.com",
            token="token",
            workspace=self.workspace,
            project=self.project,
            expires_at=timezone.now() + timezone.timedelta(days=1),
        )

        # Signup the user via invitation
        url = "/api/invitation/signup/"
        data = {
            "first_name": "user_first_name",
            "last_name": "user_last_name",
            "password": "super_complicated_password",
            "token": invitation.token,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure that the created username is lowercase
        newly_created_user = User.objects.latest("date_joined")
        self.assertEqual(newly_created_user.username, "uppercase_user@example.com")
