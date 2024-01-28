import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.user import User
from api.models.workspace import Workspace


class TestWorkspaceUserListView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        self.workspace.members.add(self.user)

    def test_user_list_workspace_user(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/workspaces/{self.workspace.id}/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Workspace.objects.count(), 1)
