import logging
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.user import User
from api.models.project import Project
from api.models.task_type import TaskType
from api.models.workspace import Workspace


class TestProjectTaskTypeListCreateView(APITestCase):
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

        self.task_type_1 = TaskType.objects.create(
            name="Follow-Up Email", project=self.project
        )
        self.task_type_2 = TaskType.objects.create(
            name="Schedule Appointment", project=self.project
        )

        self.url = f"/api/projects/{self.project.id}/task-types/"
        self.client.force_authenticate(self.user)

        return super().setUp()

    def test_list_task_types(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[1]["name"], "Follow-Up Email")
        self.assertEqual(response.json()[0]["name"], "Schedule Appointment")

    def test_create_task_type(self):
        data = {
            "name": "Send Attachment",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TaskType.objects.count(), 3)
        self.assertTrue(TaskType.objects.filter(name="Send Attachment").exists())

    def test_create_task_type_duplicate_name(self):
        data = {
            "name": "Follow-Up Email",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "A task type with name 'Follow-Up Email' already exists in this project.",
            response.json()["name"],
        )

    def test_create_task_type_in_different_project(self):
        other_project = Project.objects.create(
            name="Other Project", workspace=self.workspace
        )
        other_project.users.add(self.user)
        data = {
            "name": "Follow-Up Email",
        }
        other_project_url = f"/api/projects/{other_project.id}/task-types/"
        response = self.client.post(other_project_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TaskType.objects.count(), 3)

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
