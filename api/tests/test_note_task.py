import logging
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils.timezone import now, timedelta

from api.models.task import Task
from api.models.note import Note
from api.models.user import User
from api.models.project import Project
from api.models.task_type import TaskType
from api.models.workspace import Workspace


class TestNoteTaskListCreateView(APITestCase):
    def setUp(self):
        """Reduce log level to avoid errors like 'not found' and set up test data."""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.assignee = User.objects.create_user(
            email="assignee@gmail.com", username="assignee@gmail.com", password="password"
        )
        self.bot = User.objects.get(username="bot@raijin.ai")

        workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        workspace.members.add(self.user, through_defaults={"role": "Editor"})
        workspace.members.add(self.assignee, through_defaults={"role": "Editor"})
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)

        self.task_type = TaskType.objects.create(name="type 1", project=self.project)
        self.note = Note.objects.create(
            title="note 1", project=self.project, author=self.user
        )

        self.task1 = Task.objects.create(
            title="Task 1",
            note=self.note,
            created_by=self.user,
            type=self.task_type,
            status=Task.Status.TODO,
            priority=Task.Priority.LOW,
            due_date=now().date() + timedelta(days=1),
        )
        self.task2 = Task.objects.create(
            title="Task 2",
            note=self.note,
            created_by=self.bot,
            assigned_to=self.assignee,
            type=self.task_type,
            status=Task.Status.DONE,
            priority=Task.Priority.HIGH,
            due_date=now().date() + timedelta(days=2),
        )

        self.url = f"/api/reports/{self.note.id}/tasks/"
        self.client.force_authenticate(self.user)
        return super().setUp()

    def test_list_tasks(self):
        """Test retrieving a list of tasks for a note."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_create_task(self):
        """Test creating a task for a note."""
        data = {
            "title": "New Task",
            "type": self.task_type.id,
            "status": Task.Status.TODO,
            "priority": Task.Priority.MED,
            "due_date": (now() + timedelta(days=3)).isoformat(),
            "assigned_to": {
                "email": self.assignee.email,
            },
        }
        response = self.client.post(self.url, data=data)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_id = response.json()["id"]
        task = Task.objects.get(id=task_id)
        self.assertEqual(task.title, "New Task")
        self.assertEqual(task.priority, Task.Priority.MED)

    def test_filter_tasks_by_status(self):
        """Test filtering tasks by status."""
        response = self.client.get(f"{self.url}?status={Task.Status.TODO}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Task 1")

    def test_filter_tasks_by_priority(self):
        """Test filtering tasks by priority."""
        response = self.client.get(f"{self.url}?priority={Task.Priority.HIGH}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Task 2")

    def test_filter_tasks_by_due_date_range(self):
        """Test filtering tasks by a due date range."""
        start_date = now().date()
        end_date = now().date() + timedelta(days=2)
        response = self.client.get(
            f"{self.url}?due_date_after={start_date}&due_date_before={end_date}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)

    def test_filter_tasks_by_created_by(self):
        response = self.client.get(f"{self.url}?created_by={self.user.username}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["created_by"], self.user.first_name)

    def test_filter_tasks_by_assigned_to(self):
        response = self.client.get(f"{self.url}?assigned_to={self.assignee.username}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]["title"], "Task 1")

    def test_filter_tasks_by_bot_user(self):
        response = self.client.get(f"{self.url}?is_created_by_bot=True")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["created_by"], "Created by AI")

    def test_filter_tasks_exclude_bot_user(self):
        response = self.client.get(f"{self.url}?is_created_by_bot=False")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "Task 1")
