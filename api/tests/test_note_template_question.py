import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note_template import NoteTemplate
from api.models.project import Project
from api.models.question import Question
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectNoteListCreateView(APITestCase):
    fixtures = ["api/fixtures/note_templates.yaml"]

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
        self.outsider_project = Project.objects.create(
            name="outsider project", workspace=workspace
        )
        self.outsider_project.users.add(self.outsider)

        self.project_note_template = NoteTemplate.objects.create(
            title="project note template", project=self.project
        )
        self.question1 = Question.objects.create(
            title="question 1", project=self.project
        )
        self.question2 = Question.objects.create(
            title="question 2", project=self.project
        )
        self.project_note_template.questions.add(self.question1, self.question2)

        return super().setUp()

    def test_user_retrieve_public_note_template_questions(self):
        url = f"/api/report-templates/XdADHBwvrT3m/questions/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = [
            {
                "id": "3DiJs6oisr9Z",
                "title": "What has been happening over time? What are the trends",
            },
            {
                "id": "3a3WDxnfZA22",
                "title": "What is happening right now?",
            },
            {
                "id": "4EZKjL3USx9J",
                "title": "What's influencing these patterns?",
            },
            {
                "id": "gtZqN6HGYSXB",
                "title": "What values, beliefs or assumptions shape the system?",
            },
            {
                "id": "mgHMWaBXQQDQ",
                "title": "Where are the connections between patterns?",
            },
        ]
        self.assertCountEqual(response.json(), expected_response)

    def test_user_retrieve_project_note_template_questions(self):
        url = f"/api/report-templates/{self.project_note_template.id}/questions/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = [
            {
                "id": self.question1.id,
                "title": self.question1.title,
            },
            {
                "id": self.question2.id,
                "title": self.question2.title,
            },
        ]
        self.assertCountEqual(response.json(), expected_response)

    def test_outsider_retrieve_public_note_template_questions(self):
        url = f"/api/report-templates/XdADHBwvrT3m/questions/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_response = [
            {
                "id": "3DiJs6oisr9Z",
                "title": "What has been happening over time? What are the trends",
            },
            {
                "id": "3a3WDxnfZA22",
                "title": "What is happening right now?",
            },
            {
                "id": "4EZKjL3USx9J",
                "title": "What's influencing these patterns?",
            },
            {
                "id": "gtZqN6HGYSXB",
                "title": "What values, beliefs or assumptions shape the system?",
            },
            {
                "id": "mgHMWaBXQQDQ",
                "title": "Where are the connections between patterns?",
            },
        ]
        self.assertCountEqual(response.json(), expected_response)

    def test_outsider_retrieve_project_note_template_questions(self):
        url = f"/api/report-templates/{self.project_note_template.id}/questions/"
        self.client.force_authenticate(self.outsider)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
