import logging

from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.task import Task
from api.models.task_type import TaskType
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectTaskListView(APITestCase):
    def setUp(self):
        """Reduce log level to avoid errors like 'not found' and set up test data."""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.assignee = User.objects.create_user(
            username="assignee", password="password"
        )
        self.bot = User.objects.get(username="bot@raijin.ai")

        workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        workspace.members.add(self.user, through_defaults={"role": "Editor"})
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)

        self.task_type = TaskType.objects.create(name="type 1", project=self.project)

        self.note = Note.objects.create(
            title="note 1", project=self.project, author=self.user, is_approved=True
        )

        self.task1 = Task.objects.create(
            title="Task 1",
            note=self.note,
            created_by=self.user,
            type=self.task_type,
            status=Task.Status.TODO,
            priority=Task.Priority.LOW,
            due_date=timezone.now() + timedelta(days=1),
        )
        self.task2 = Task.objects.create(
            title="Task 2",
            note=self.note,
            created_by=self.bot,
            type=self.task_type,
            status=Task.Status.DONE,
            priority=Task.Priority.HIGH,
            due_date=timezone.now() + timedelta(days=2),
        )

        self.url = f"/api/projects/{self.project.id}/tasks/"
        self.client.force_authenticate(self.user)
        return super().setUp()

    def test_list_tasks(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_filter_tasks_by_status(self):
        response = self.client.get(f"{self.url}?status={Task.Status.TODO}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["status"], "Todo")
        self.assertEqual(response.json()[0]["title"], "Task 1")

    def test_filter_tasks_by_priority(self):
        response = self.client.get(f"{self.url}?priority={Task.Priority.HIGH}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["priority"], "High")
        self.assertEqual(response.json()[0]["title"], "Task 2")

    def test_filter_tasks_by_bot_user(self):
        response = self.client.get(f"{self.url}?is_created_by_bot=True")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["created_by"], "Created by AI")
        self.assertEqual(response.json()[0]["title"], "Task 2")

    def test_filter_tasks_exclude_bot_user(self):
        response = self.client.get(f"{self.url}?is_created_by_bot=False")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Task 1")
