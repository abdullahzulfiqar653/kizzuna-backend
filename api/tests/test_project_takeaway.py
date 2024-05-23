import logging

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectTakeawayListView(APITestCase):
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

        self.note1 = Note.objects.create(
            title="note 1", project=self.project, author=self.user, type="note type 1"
        )
        self.takeaway_type1 = TakeawayType.objects.create(
            name="takeaway type 1", project=self.project
        )
        self.takeaway1 = Takeaway.objects.create(
            title="takeaway 1",
            note=self.note1,
            created_by=self.user,
            type=self.takeaway_type1,
            priority="High",
            vector=np.random.rand(1536),
        )

        self.note2 = Note.objects.create(
            title="note 1", project=self.project, author=self.user, type="note type 2"
        )
        self.takeaway_type2 = TakeawayType.objects.create(
            name="takeaway type 2", project=self.project
        )
        self.takeaway2 = Takeaway.objects.create(
            title="takeaway 2",
            note=self.note2,
            created_by=self.user,
            type=self.takeaway_type2,
            priority="Low",
            vector=np.random.rand(1536),
        )

        self.url = f"/api/projects/{self.project.id}/takeaways/"
        return super().setUp()

    def test_user_list_project_takeaways(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_takeaway_ids = [takeaway["id"] for takeaway in response.json()]
        self.assertCountEqual(
            response_takeaway_ids, [self.takeaway1.id, self.takeaway2.id]
        )

    def test_user_list_project_takeaways_filter_note(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}?report_id={self.note1.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_takeaway_ids = [takeaway["id"] for takeaway in response.json()]
        self.assertCountEqual(response_takeaway_ids, [self.takeaway1.id])

    def test_user_list_project_takeaways_filter_note_type(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}?report_type={self.note1.type}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_takeaway_ids = [takeaway["id"] for takeaway in response.json()]
        self.assertCountEqual(response_takeaway_ids, [self.takeaway1.id])

    def test_user_list_project_takeaways_filter_priority(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}?priority=High")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_takeaway_ids = [takeaway["id"] for takeaway in response.json()]
        self.assertCountEqual(response_takeaway_ids, [self.takeaway1.id])

    def test_user_list_project_takeaways_filter_takeaway_type(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}?type=takeaway%20type%202")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_takeaway_ids = [takeaway["id"] for takeaway in response.json()]
        self.assertCountEqual(response_takeaway_ids, [self.takeaway2.id])
