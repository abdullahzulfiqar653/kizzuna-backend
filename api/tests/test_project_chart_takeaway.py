import logging

import numpy as np
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.keyword import Keyword
from api.models.note import Note
from api.models.organization import Organization
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestSavedTakeawayView(APITestCase):
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

        self.note1 = Note.objects.create(
            title="note 1", project=self.project, author=self.user
        )
        self.note2 = Note.objects.create(
            title="note 2", project=self.project, author=self.user
        )

        self.takeaway1 = Takeaway.objects.create(
            title="takeaway 1",
            note=self.note1,
            created_by=self.user,
            vector=np.random.rand(1536),
        )
        self.takeaway2 = Takeaway.objects.create(
            title="takeaway 2",
            note=self.note1,
            created_by=self.user,
            vector=np.random.rand(1536),
        )
        self.takeaway3 = Takeaway.objects.create(
            title="takeaway 3",
            note=self.note2,
            created_by=self.user,
            vector=np.random.rand(1536),
        )

        organization = Organization.objects.create(
            name="organization", project=self.project
        )
        self.note1.organizations.add(organization)

        keyword = Keyword.objects.create(name="keyword")
        self.note2.keywords.add(keyword)
        return super().setUp()

    def test_user_count_note(self):
        data = {
            "filter": {},
            "group_by": [
                {"field": "type_name"},
                {"field": "tag"},
                {"field": "created_by_username"},
                {"field": "created_by_first_name"},
                {"field": "created_by_last_name"},
                {"field": "priority"},
                {"field": "report"},
                {"field": "report_keyword"},
                {"field": "report_title"},
                {"field": "report_type"},
                {"field": "report_sentiment"},
                {"field": "created_at"},
            ],
            "aggregate": {
                "field": "takeaway",
                "function": "count",
                "distinct": True,
            },
        }
        url = f"/api/projects/{self.project.id}/charts/takeaways/"
        self.client.force_authenticate(self.user)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_outsider_count_note(self):
        data = {
            "filter": {},
            "group_by": [
                {"field": "organization"},
                {"field": "type"},
                {"field": "revenue"},
                {"field": "sentiment"},
                {"field": "author_username"},
                {"field": "author_first_name"},
                {"field": "author_last_name"},
                {"field": "keyword"},
                {"field": "created_at"},
            ],
            "aggregate": {
                "field": "report",
                "function": "count",
                "distinct": True,
            },
        }
        url = f"/api/projects/{self.project.id}/charts/takeaways/"
        self.client.force_authenticate(self.outsider)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
