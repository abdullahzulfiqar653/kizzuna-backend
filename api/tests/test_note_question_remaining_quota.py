import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.question import Question
from api.models.user import User
from api.models.workspace import Workspace


class TestNoteQuestionRemainingQuotaRetrieveView(APITestCase):
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
            title="note 1", project=self.project, author=self.user
        )
        self.question1 = Question.objects.create(
            title="question 1", project=self.project
        )
        self.question2 = Question.objects.create(
            title="question 2", project=self.project
        )
        self.note.questions.add(
            self.question1,
            self.question2,
            through_defaults=dict(created_by=self.user),
        )
        return super().setUp()

    def test_user_retrieve_remaining_quota(self):
        url = f"/api/reports/{self.note.id}/questions/remaining-quotas/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["value"], 3)

    def test_user_retrieve_remaining_quota_that_exceeded_on_another_note(self):
        """
        This test is to make sure that the remaining quota is not affected by
        other notes.
        """
        # Creating question on another note
        self.another_note = Note.objects.create(
            title="note 2", project=self.project, author=self.user
        )
        questions = [
            Question.objects.create(
                title=f"question {i} in another note", project=self.project
            )
            for i in range(5)
        ]
        self.another_note.questions.add(
            *questions, through_defaults=dict(created_by=self.user)
        )

        # Ensure that no remaining quota on another note
        url = f"/api/reports/{self.another_note.id}/questions/remaining-quotas/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["value"], 0)

        # Ensure that there are still quota on this note
        url = f"/api/reports/{self.note.id}/questions/remaining-quotas/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["value"], 3)

    def test_user_retrieve_remaining_quota_not_go_below_zero(self):
        """
        This test is to make sure that the remaining quota is not affected by
        other notes.
        """
        # Creating question on another note
        questions = [
            Question.objects.create(title=f"question {i}", project=self.project)
            for i in range(3, 10)
        ]
        self.note.questions.add(*questions, through_defaults=dict(created_by=self.user))

        # Ensure that no remaining quota on another note
        url = f"/api/reports/{self.note.id}/questions/remaining-quotas/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["value"], 0)
