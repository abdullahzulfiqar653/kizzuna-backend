import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.user import User


class TestUserRetrieveUpdateDestroyView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        self.workspace = self.user.owned_workspaces.create(name="owned workspace")
        self.user.workspaces.add(self.workspace)
        self.outsider_owned_workspace = self.outsider.owned_workspaces.create(
            name="outsider owned workspace"
        )
        self.user.workspaces.add(self.outsider_owned_workspace)
        self.outsider.workspaces.add(self.outsider_owned_workspace)

    def test_user_retrieve_profile(self):
        url = "/api/auth-users/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {
            "email": "",
            "first_name": "",
            "last_name": "",
            "workspaces": [
                {
                    "is_owner": True,
                    "id": self.workspace.id,
                    "name": self.workspace.name,
                },
                {
                    "is_owner": False,
                    "id": self.outsider_owned_workspace.id,
                    "name": self.outsider_owned_workspace.name,
                },
            ],
            "skip_tutorial": False,
            "consent_given": False,
        }
        self.assertEqual(response.json(), expected_data)

    def test_outsider_retrieve_profile(self):
        url = "/api/auth-users/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {
            "email": "",
            "first_name": "",
            "last_name": "",
            "workspaces": [
                {
                    "is_owner": True,
                    "id": self.outsider_owned_workspace.id,
                    "name": self.outsider_owned_workspace.name,
                },
            ],
            "skip_tutorial": False,
            "consent_given": False,
        }
        self.assertEqual(response.json(), expected_data)

    def test_anon_retrieve_profile(self):
        url = "/api/auth-users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
