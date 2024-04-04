import logging
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.question import Question
from api.models.user import User
from api.models.workspace import Workspace


class TestNoteQuestionListCreateView(APITestCase):
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
        self.note.questions.add(self.question1, self.question2)
        return super().setUp()

    def test_user_list_report_questions(self):
        url = f"/api/reports/{self.note.id}/questions/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_question_ids = [question["id"] for question in response.json()]
        self.assertCountEqual(
            response_question_ids, [self.question1.id, self.question2.id]
        )

    @patch("api.tasks.ask_note_question.delay")
    def test_user_create_report_question(self, mocked_delay):
        url = f"/api/reports/{self.note.id}/questions/"
        self.client.force_authenticate(self.user)
        data = {
            "title": "question 3",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        question_id = response.json()["id"]
        mocked_delay.assert_called_once_with(self.note.id, question_id, self.user.id)

        # Make sure to record the note question is created by the user
        note_question = self.note.questions.through.objects.get(question_id=question_id)
        self.assertEqual(note_question.created_by, self.user)

    def test_user_create_existing_report_question(self):
        url = f"/api/reports/{self.note.id}/questions/"
        self.client.force_authenticate(self.user)
        data = {
            "title": "question 1",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_create_report_question_more_than_quota(self):
        user_questions = [
            Question.objects.create(title=f"user question {i}", project=self.project)
            for i in range(1, 6)
        ]
        self.note.questions.add(
            *user_questions, through_defaults={"created_by": self.user}
        )

        url = f"/api/reports/{self.note.id}/questions/"
        self.client.force_authenticate(self.user)
        data = {
            "title": "user question 6",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch("api.tasks.ask_note_question.delay")
    def test_user_create_report_question_quota_exceeded_on_another_note(
        self, mocked_delay
    ):
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

        # Ensure that there are still quota on this note
        url = f"/api/reports/{self.note.id}/questions/"
        self.client.force_authenticate(self.user)
        data = {
            "title": "question 3",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        question_id = response.json()["id"]
        mocked_delay.assert_called_once_with(self.note.id, question_id, self.user.id)

    def test_outsider_create_report_question(self):
        url = f"/api/reports/{self.note.id}/questions/"
        self.client.force_authenticate(self.outsider)
        data = {
            "title": "question 3",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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
