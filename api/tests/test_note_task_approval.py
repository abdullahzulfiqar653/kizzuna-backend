from rest_framework import status
from rest_framework.test import APITestCase
from api.models import Note, Task, User, Workspace, Project, TaskType
from django.utils.timezone import now, timedelta
import logging


class NoteTaskApprovalCreateViewTests(APITestCase):

    def setUp(self):
        """Set up test data with bot user for task creation."""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(
            email="test@example.com", username="test@example.com", password="password"
        )
        self.assignee = User.objects.create_user(
            email="assignee@gmail.com",
            username="assignee@gmail.com",
            password="password",
        )
        self.bot = User.objects.get(username="bot@raijin.ai")

        workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        workspace.members.add(self.user, through_defaults={"role": "Editor"})
        workspace.members.add(self.assignee, through_defaults={"role": "Editor"})

        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)

        self.task_type = TaskType.objects.create(name="Task Type", project=self.project)
        self.note = Note.objects.create(
            title="Test Note", project=self.project, author=self.user, is_approved=False
        )

        self.task1 = Task.objects.create(
            title="Task 1",
            note=self.note,
            created_by=self.bot,
            type=self.task_type,
            status=Task.Status.TODO,
            priority=Task.Priority.LOW,
            due_date=now() + timedelta(days=1),
        )

        self.task2 = Task.objects.create(
            title="Task 2",
            note=self.note,
            created_by=self.bot,
            type=self.task_type,
            status=Task.Status.TODO,
            priority=Task.Priority.MED,
            due_date=now() + timedelta(days=2),
        )

        self.url = f"/api/reports/{self.note.id}/tasks/approve/"
        self.client.force_authenticate(self.user)

    def test_approve_note_with_tasks(self):
        """Test approving a note with task approval."""

        data = {"task_ids": [str(self.task1.id)]}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.note.refresh_from_db()
        self.assertTrue(self.note.is_approved)
        remaining_tasks = Task.objects.filter(note=self.note)
        self.assertEqual(remaining_tasks.count(), 1)
        self.assertEqual(remaining_tasks.first().id, self.task1.id)

    def test_approve_already_approved_note(self):
        self.note.is_approved = True
        self.note.save()

        data = {"task_ids": [self.task1.id, self.task2.id]}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Note is already approved")

    def test_approve_note_without_tasks(self):
        data = {"task_ids": []}

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.note.refresh_from_db()

        self.assertTrue(self.note.is_approved)
        remaining_tasks = Task.objects.filter(note=self.note)
        self.assertEqual(remaining_tasks.count(), 0)
