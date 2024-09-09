import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.user import User


class TestSignupView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)
        return super().setUp()

    def test_user_signup(self):
        url = "/api/signup/"
        data = {
            "username": "user@example.com",
            "password": "somercomplexpassword",
            "email": "user@example.com",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)  # 1 user AI bot is created by default
        self.assertTrue(User.objects.filter(username="user@example.com").exists())


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
                    "id": self.workspace.id,
                    "name": self.workspace.name,
                    "is_owner": True,
                    "industry": "",
                    "company_size": "",
                    "subscription_type": "",
                    "subscription_name": None,
                    "subscription_end_at": None,
                    "subscription_is_free_trial": None,
                },
                {
                    "id": self.outsider_owned_workspace.id,
                    "name": self.outsider_owned_workspace.name,
                    "is_owner": False,
                    "industry": "",
                    "company_size": "",
                    "subscription_type": "",
                    "subscription_name": None,
                    "subscription_end_at": None,
                    "subscription_is_free_trial": None,
                },
            ],
            "skip_tutorial": False,
            "consent_given": False,
            "job": "",
            "tutorial": {},
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
                    "id": self.outsider_owned_workspace.id,
                    "name": self.outsider_owned_workspace.name,
                    "is_owner": True,
                    "industry": "",
                    "company_size": "",
                    "subscription_type": "",
                    "subscription_name": None,
                    "subscription_end_at": None,
                    "subscription_is_free_trial": None,
                }
            ],
            "skip_tutorial": False,
            "consent_given": False,
            "job": "",
            "tutorial": {},
        }
        self.assertEqual(response.json(), expected_data)

    def test_anon_retrieve_profile(self):
        url = "/api/auth-users/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
