import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.user import User
from api.models.workspace import Workspace


class TestWorkspaceListCreateView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")

    def test_anon_create_workspace(self):
        response = self.client.post("/api/workspaces/", {"name": "workspace name"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_list_workspace(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/workspaces/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Workspace.objects.count(), 0)

    def test_user_create_workspace(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/workspaces/", {"name": "workspace name"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Workspace.objects.count(), 1)

    def test_user_create_workspace_with_colliding_name(self):
        Workspace.objects.create(name="colliding workspace name", owned_by=self.user)
        self.client.force_authenticate(self.user)
        response = self.client.post(
            "/api/workspaces/", {"name": "colliding workspace name"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Workspace.objects.count(), 1)
