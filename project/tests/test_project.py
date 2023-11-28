import logging

from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from note.models import Note
from project.models import Project
from workspace.models import Workspace


class TestProjectRetrieveUpdateDeleteView(APITestCase):
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
        self.url = f"/api/projects/{self.project.id}/"
        return super().setUp()

    def test_user_retrieve_project_has_usage(self):
        """
        Test if the usage data exists in the endpoint response payload.
        """
        Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
            file_duration_seconds=118,
            analyzing_tokens=150,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        workspace_data = response.json()["workspace"]
        expected_usage_data = {"usage_minutes": 2, "usage_tokens": 150}
        self.assertTrue(workspace_data.items() >= expected_usage_data.items())

    def test_user_retrieve_project_usage_calculation_multiple_notes(self):
        """
        Test usage calculation sum usage minutes and usage tokens
        over multiple notes properly.
        """
        Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
            file_duration_seconds=118,
            analyzing_tokens=150,
        )
        Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
            file_duration_seconds=435,
            analyzing_tokens=542,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        workspace_data = response.json()["workspace"]
        expected_usage_minutes = round((118 + 435) / 60.0)
        expected_usage_tokens = 150 + 542
        expected_usage_data = {
            "usage_minutes": expected_usage_minutes,
            "usage_tokens": expected_usage_tokens,
        }
        self.assertTrue(workspace_data.items() >= expected_usage_data.items())

    def test_user_retrieve_project_usage_calculation_multiple_projects(self):
        """
        Test usage calculation can handle notes in multiple projects.
        """
        Note.objects.create(
            title="note",
            project=self.project,
            author=self.user,
            file_duration_seconds=118,
            analyzing_tokens=150,
        )
        another_project = Project.objects.create(
            name="project", workspace=self.project.workspace
        )
        Note.objects.create(
            title="note",
            project=another_project,
            author=self.user,
            file_duration_seconds=435,
            analyzing_tokens=542,
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        workspace_data = response.json()["workspace"]
        expected_usage_minutes = round((118 + 435) / 60.0)
        expected_usage_tokens = 150 + 542
        expected_usage_data = {
            "usage_minutes": expected_usage_minutes,
            "usage_tokens": expected_usage_tokens,
        }
        self.assertTrue(workspace_data.items() >= expected_usage_data.items())
