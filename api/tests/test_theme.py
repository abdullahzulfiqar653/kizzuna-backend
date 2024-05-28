import logging

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.asset import Asset
from api.models.block import Block
from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.theme import Theme
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestThemeRetrieveUpdateDestroyView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        self.workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        self.workspace.members.add(self.user, through_defaults={"role": "Editor"})
        self.project = Project.objects.create(name="project", workspace=self.workspace)
        self.project.users.add(self.user)

        self.note = Note.objects.create(
            title="note", project=self.project, author=self.user
        )
        self.takeaway1 = Takeaway.objects.create(
            title="takeaway 1",
            note=self.note,
            created_by=self.user,
            vector=np.random.rand(1536),
        )
        self.takeaway2 = Takeaway.objects.create(
            title="takeaway 2",
            note=self.note,
            created_by=self.user,
            vector=np.random.rand(1536),
        )

        self.asset = Asset.objects.create(
            title="asset", project=self.project, created_by=self.user
        )
        self.theme_block = Block.objects.create(
            type=Block.Type.THEMES,
            asset=self.asset,
        )
        self.asset.blocks.add(self.theme_block)

        # Create themes and add it to the theme_block
        self.theme1 = Theme.objects.create(
            title="theme 1",
            block=self.theme_block,
        )
        self.theme2 = Theme.objects.create(
            title="theme 2",
            block=self.theme_block,
        )

    def test_user_retrieve_theme(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/themes/{self.theme1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.theme1.title)

    def test_user_update_theme(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f"/api/themes/{self.theme1.id}/", {"title": "new theme"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.theme1.refresh_from_db()
        self.assertEqual(self.theme1.title, "new theme")

    def test_user_delete_theme(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f"/api/themes/{self.theme1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Theme.objects.filter(id=self.theme1.id).exists())

    def test_user_update_theme_order(self):
        self.assertEqual(self.theme1.order, 0)
        self.assertEqual(self.theme2.order, 1)
        self.client.force_authenticate(self.user)
        url = f"/api/themes/{self.theme2.id}/"
        data = {"order": 0}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that text block order is also updated
        self.theme1.refresh_from_db()
        self.theme2.refresh_from_db()
        self.assertEqual(self.theme2.order, 0)
        self.assertEqual(self.theme1.order, 1)
