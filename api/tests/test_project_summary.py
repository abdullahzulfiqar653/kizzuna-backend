import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectSummaryRetrieveView(APITestCase):
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
        workspace.members.add(self.user, through_defaults={"role": "Editor"})
        self.project = Project.objects.create(
            name="project",
            workspace=workspace,
            summary="project summary",
            key_themes=[
                {
                    "title": "key theme 1",
                    "takeaways": [
                        "key theme 1 takeaway 1",
                        "key theme 1 takeaway 2",
                    ],
                },
                {
                    "title": "key theme 2",
                    "takeaways": [
                        "key theme 2 takeaway 1",
                        "key theme 2 takeaway 2",
                    ],
                },
            ],
        )
        self.project.users.add(self.user)

        return super().setUp()

    def test_user_retrieve_project_summary(self):
        url = f"/api/projects/{self.project.id}/summary/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.json(),
            {
                "summary": "project summary",
                "key_themes": [
                    {
                        "title": "key theme 1",
                        "takeaways": [
                            "key theme 1 takeaway 1",
                            "key theme 1 takeaway 2",
                        ],
                    },
                    {
                        "title": "key theme 2",
                        "takeaways": [
                            "key theme 2 takeaway 1",
                            "key theme 2 takeaway 2",
                        ],
                    },
                ],
            },
        )

    def test_outsider_retrieve_project_summary(self):
        url = f"/api/projects/{self.project.id}/summary/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
