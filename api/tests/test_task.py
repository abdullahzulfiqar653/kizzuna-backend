import logging
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta

from api.models.user import User
from api.models.task import Task
from api.models.note import Note
from api.models.project import Project
from api.models.task_type import TaskType
from api.models.workspace import Workspace


class TestTaskRetrieveUpdateDeleteView(APITestCase):
    def setUp(self):
        """Reduce log level to avoid errors and set up test data."""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.other_user = User.objects.create_user(
            username="other_user", password="password"
        )
        self.workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        self.workspace.members.add(self.user, through_defaults={"role": "Editor"})

        self.project = Project.objects.create(name="project", workspace=self.workspace)
        self.project.users.add(self.user)
        self.note = Note.objects.create(
            title="note 1", project=self.project, author=self.user
        )
        self.task_type = TaskType.objects.create(
            name="Follow-Up Email",
            project=self.project,
            definition="Sending a follow-up email.",
        )

        self.task = Task.objects.create(
            title="Test Task",
            description="This is a test task.",
            type=self.task_type,
            created_by=self.user,
            due_date=timezone.now() + timedelta(days=1),
            priority=Task.Priority.HIGH,
            status=Task.Status.TODO,
            note=self.note,
        )
        self.url = f"/api/tasks/{self.task.id}/"
        self.client.force_authenticate(self.user)
        return super().setUp()

    def test_retrieve_task(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Task")
        self.assertEqual(response.data["description"], "This is a test task.")
        self.assertEqual(response.data["priority"], "High")
        self.assertEqual(response.data["status"], "Todo")
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)
        self.assertEqual(response.data["created_by"], self.user.first_name)

    def test_update_task(self):
        data = {
            "title": "Updated Task Title",
            "description": "Updated description.",
            "priority": Task.Priority.MED,
            "status": Task.Status.OVERDUE,
        }
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Task Title")
        self.assertEqual(response.data["description"], "Updated description.")
        self.assertEqual(response.data["priority"], "Med")
        self.assertEqual(response.data["status"], "Overdue")
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated Task Title")
        self.assertEqual(self.task.description, "Updated description.")
        self.assertEqual(self.task.priority, Task.Priority.MED)
        self.assertEqual(self.task.status, Task.Status.OVERDUE)

    def test_delete_task(self):
        """Test that a task can be deleted by ID."""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify that the task was deleted from the database
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_validate_assigned_to(self):
        """Test that validation for assigned user works correctly."""
        user = User.objects.create_user(
            username="newuser@example.com",
            email="newuser@example.com",
            password="password",
        )
        self.project.users.add(user)
        data = {
            "title": "Task with Assignee",
            "assigned_to": {"email": "newuser@example.com"},
            "type": {"name": "Follow-Up Email"},
        }
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Task.objects.last().assigned_to, user)

    def test_invalid_assigned_to(self):
        data = {
            "title": "Task with Invalid Assignee",
            "assigned_to": {"email": "nonexistentuser@example.com"},
            "type": {"name": "Follow-Up Email"},
        }
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Assignee User does not exist in project.", response.data["assigned_to"]
        )

    def test_validate_type(self):
        data = {
            "title": "Task with Invalid Type",
            "type": {"name": "Nonexistent Task Type"},
        }
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Task type does not exist in project.", response.data["type"])

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the view."""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
