import logging
import unittest

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.keyword import Keyword
from api.models.note import Note
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectNoteListCreateView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        workspace = Workspace.objects.create(name="workspace")
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)
        return super().setUp()

    def test_user_list_report_filter_type(self):
        Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            type="Report-type-1",
        )
        Note.objects.create(
            title="Sample report with the same type",
            project=self.project,
            author=self.user,
            type="Report-type-1",
        )
        Note.objects.create(
            title="Sample report with a different type",
            project=self.project,
            author=self.user,
            type="Report-type-2",
        )
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/?type=Report-type-1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_user_list_report_filter_keyword(self):
        note_with_keyword = Note.objects.create(
            title="Report with keyword",
            project=self.project,
            author=self.user,
        )
        keyword = Keyword.objects.create(name="keyword")
        note_with_keyword.keywords.add(keyword)

        Note.objects.create(
            title="Report without keyword",
            project=self.project,
            author=self.user,
        )

        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/?keyword=keyword"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], note_with_keyword.id)

    def test_user_list_report_search(self):
        Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            type="Report-type-1",
        )
        Note.objects.create(
            title="Sample report with search term",
            project=self.project,
            author=self.user,
            type="Report-type-1",
        )
        Note.objects.create(
            title="Another sample report with search term",
            project=self.project,
            author=self.user,
            type="Report-type-2",
        )
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/?search=search%20term"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_user_create_report(self):
        data = {
            "title": "User can create report.",
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
        }
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Check that organization is created
        response_json = response.json()
        note = Note.objects.get(id=response_json["id"])
        self.assertEqual(note.organizations.count(), 1)

    @unittest.expectedFailure
    def test_user_create_report_exceed_usage_minutes(self):
        Note.objects.create(
            title="Use up all usage minutes.",
            project=self.project,
            author=self.user,
            file_duration_seconds=61 * 60,
        )
        data = {
            "title": "Attempt to add one more report",
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
        }
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @unittest.expectedFailure
    def test_user_create_report_exceed_usage_tokens(self):
        Note.objects.create(
            title="Use up all usage minutes.",
            project=self.project,
            author=self.user,
            analyzing_tokens=51_000,
        )
        data = {
            "title": "Attempt to add one more report",
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
        }
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Assert that the endpoint doesn't create the note.
        self.assertEqual(self.project.notes.count(), 1)

    def test_user_create_report_without_organizations(self):
        data = {
            "title": "Add report without organizations info.",
        }
        self.client.force_authenticate(self.user)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_outsider_create_report(self):
        data = {
            "title": "Attempt to add report without permission.",
            "organizations": [
                {
                    "name": "Test company",
                }
            ],
        }
        self.client.force_authenticate(self.outsider)
        url = f"/api/projects/{self.project.id}/reports/"
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        # Assert that the endpoint doesn't create the note.
        self.assertEqual(self.project.notes.count(), 0)
