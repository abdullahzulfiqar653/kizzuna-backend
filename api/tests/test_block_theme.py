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
class TestBlockThemeListCreateView(APITestCase):
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
        self.takeaways_block = Block.objects.create(
            type=Block.Type.TAKEAWAYS,
            asset=self.asset,
        )
        self.theme_block = Block.objects.create(
            type=Block.Type.THEMES,
            asset=self.asset,
        )
        self.asset.blocks.add(self.theme_block)

        # Create a theme and add it to the theme_block
        self.theme = Theme.objects.create(
            title="theme",
            block=self.theme_block,
        )

    def test_user_list_block_themes(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/blocks/{self.theme_block.id}/themes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the theme is in the response
        self.assertEqual(len(response.json()), 1)

    def test_user_create_block_theme(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f"/api/blocks/{self.theme_block.id}/themes/",
            data={"title": "new theme"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check if the theme is added to the block
        self.assertEqual(self.theme_block.themes.count(), 2)

    def test_user_create_theme_in_takeaways_block(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            f"/api/blocks/{self.takeaways_block.id}/themes/",
            data={"title": "new theme"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check if the theme is not added to the block
        self.assertEqual(self.takeaways_block.themes.count(), 0)
        self.assertEqual(self.theme_block.themes.count(), 1)

    def test_outsider_create_block_theme(self):
        self.client.force_authenticate(user=self.outsider)
        response = self.client.post(
            f"/api/blocks/{self.theme_block.id}/themes/",
            data={"title": "new theme"},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Check if the theme is not added to the block
        self.assertEqual(self.theme_block.themes.count(), 1)