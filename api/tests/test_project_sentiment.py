import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectSentimentListView(APITestCase):
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
        self.url = f"/api/projects/{self.project.id}/sentiments/"
        return super().setUp()

    def test_user_list_report_sentiments_in_project(self):
        Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            sentiment="Positive",
        )
        Note.objects.create(
            title="Sample report with a different sentiment",
            project=self.project,
            author=self.user,
            sentiment="Neutral",
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_results = [
            {"name": "Neutral", "report_count": 1},
            {"name": "Positive", "report_count": 1},
        ]
        self.assertEqual(response.json(), expected_results)

    def test_user_list_report_sentiments_in_project_with_search(self):
        Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            sentiment="Positive",
        )
        Note.objects.create(
            title="Sample report with a different sentiment",
            project=self.project,
            author=self.user,
            sentiment="Neutral",
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(f"{self.url}?search=Positive")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_results = [{"name": "Positive", "report_count": 1}]
        self.assertEqual(response.json(), expected_results)
