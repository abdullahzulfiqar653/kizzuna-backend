import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.feature import Feature
from api.models.user import User
from api.models.workspace import Workspace
from api.models.workspace_user import WorkspaceUser


class TestWorkspaceUserListUpdateView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.owner = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="password",
        )
        self.workspace = Workspace.objects.create(name="workspace", owned_by=self.owner)
        self.workspace.members.add(
            self.owner, through_defaults={"role": WorkspaceUser.Role.OWNER}
        )

        self.editor = User.objects.create_user(
            username="editor@example.com",
            email="editor@example.com",
            password="password",
        )
        self.workspace.members.add(
            self.editor, through_defaults={"role": WorkspaceUser.Role.EDITOR}
        )

        self.viewer = User.objects.create_user(
            username="viewer@example.com",
            email="viewer@example.com",
            password="password",
        )
        self.workspace.members.add(
            self.viewer, through_defaults={"role": WorkspaceUser.Role.VIEWER}
        )

    def test_editor_list_workspace_user(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(f"/api/workspaces/{self.workspace.id}/users/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [
            {
                "user": {
                    "email": self.owner.email,
                    "first_name": "",
                    "last_name": "",
                },
                "role": WorkspaceUser.Role.OWNER,
            },
            {
                "user": {
                    "email": self.editor.email,
                    "first_name": "",
                    "last_name": "",
                },
                "role": WorkspaceUser.Role.EDITOR,
            },
            {
                "user": {
                    "email": self.viewer.email,
                    "first_name": "",
                    "last_name": "",
                },
                "role": WorkspaceUser.Role.VIEWER,
            },
        ]
        self.assertCountEqual(response.json(), expected_data)

    def test_owner_update_viewer_role(self):
        # Increase the number of editors allowed in the workspace
        feature = Feature.objects.get(code=Feature.Code.NUMBER_OF_EDITORS)
        feature.default = 3
        feature.save()

        url = f"/api/workspaces/{self.workspace.id}/users/"
        self.client.force_authenticate(self.owner)
        data = {"username": self.viewer.username, "role": "Editor"}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.viewer.refresh_from_db()
        role = WorkspaceUser.objects.get(
            user=self.viewer, workspace=self.workspace
        ).role
        self.assertEqual(role, "Editor")

    def test_owner_update_role_to_owner(self):
        """
        Cannot assign owner role to a user
        """
        url = f"/api/workspaces/{self.workspace.id}/users/"
        self.client.force_authenticate(self.owner)
        data = {"username": self.viewer.username, "role": "Owner"}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_update_owner_role(self):
        """
        Cannot change the role of the workspace owner
        """
        url = f"/api/workspaces/{self.workspace.id}/users/"
        self.client.force_authenticate(self.owner)
        data = {"username": self.owner.username, "role": "Editor"}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_editor_update_viewer_role(self):
        url = f"/api/workspaces/{self.workspace.id}/users/"
        self.client.force_authenticate(self.editor)
        data = {"username": self.viewer.username, "role": "Editor"}
        response = self.client.patch(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
