import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.keyword import Keyword
from api.models.note import Note
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectKeywordListView(APITestCase):
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
        self.url = f"/api/projects/{self.project.id}/keywords/"

    def test_user_list_only_report_keywords_in_project(self):
        """
        To test that the endpoint does not list the keywords in another project.
        """
        note_in_project = Note.objects.create(
            title="report in project", project=self.project, author=self.user
        )
        keyword_in_project = Keyword.objects.create(name="keyword in project")
        note_in_project.keywords.add(keyword_in_project)

        another_project = Project.objects.create(
            name="another project", workspace=self.workspace
        )
        another_project.users.add(self.user)
        note_in_another_project = Note.objects.create(
            title="report in another project", project=another_project, author=self.user
        )
        keyword_in_another_project = Keyword.objects.create(
            name="keyword in another project"
        )
        note_in_another_project.keywords.add(keyword_in_another_project)

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_results = [
            {
                "id": keyword_in_project.id,
                "name": keyword_in_project.name,
                "report_count": 1,
            }
        ]
        self.assertEqual(response.json(), expected_results)

    def test_user_list_non_duplicated_report_keywords_in_project(self):
        """
        To test that when same keyword appear in multiple reports, the list is dedup.
        """
        note_in_project = Note.objects.create(
            title="report in project", project=self.project, author=self.user
        )
        keyword_in_project = Keyword.objects.create(name="keyword in project")
        note_in_project.keywords.add(keyword_in_project)

        another_note_in_project = Note.objects.create(
            title="report in another project", project=self.project, author=self.user
        )
        another_note_in_project.keywords.add(keyword_in_project)

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
