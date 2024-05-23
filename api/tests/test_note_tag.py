import logging

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.user import User
from api.models.workspace import Workspace


class TestNoteTagListView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        self.project = Project.objects.create(name="project", workspace=workspace)
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

        self.tag1 = Tag.objects.create(
            name="tag 1",
            project=self.project,
        )
        self.tag2 = Tag.objects.create(
            name="tag 2",
            project=self.project,
        )

        self.takeaway1.tags.add(self.tag1)
        self.takeaway1.tags.add(self.tag2)
        self.takeaway2.tags.add(self.tag1)

        self.url = f"/api/reports/{self.note.id}/tags/"
        return super().setUp()

    def test_user_list_report_tags(self):
        expected_data = [
            {
                "id": self.tag1.id,
                "name": self.tag1.name,
                "project": self.tag1.project.id,
                "takeaway_count": 2,
            },
            {
                "id": self.tag2.id,
                "name": self.tag2.name,
                "project": self.tag2.project.id,
                "takeaway_count": 1,
            },
        ]

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.json(), expected_data)

    def test_outsider_list_report_tags(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
