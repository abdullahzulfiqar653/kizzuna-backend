import logging
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse

from api.models.user import User
from api.models.project import Project
from api.models.task_type import TaskType
from api.models.workspace import Workspace


class TestTaskTypeRetrieveUpdateDestroyView(APITestCase):
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
            name="Follow-Up Email",
            project=self.project,
            definition="Sending a follow-up email.",
        )
        self.task_type_2 = TaskType.objects.create(
            name="Schedule Appointment",
            project=self.project,
            definition="Schedule a meeting.",
        )
        self.url = reverse(
            "takeaway-type-retrieve-update-destroy", kwargs={"pk": self.task_type_1.id}
        )
        self.url = f"/api/task-types/{self.task_type_1.id}/"
        self.client.force_authenticate(self.user)
        return super().setUp()

    def test_retrieve_task_type(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Follow-Up Email")
        self.assertEqual(response.data["definition"], "Sending a follow-up email.")
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    def test_update_task_type(self):
        data = {"name": "Updated Task Type", "definition": "Updated definition."}
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Task Type")
        self.assertEqual(response.data["definition"], "Updated definition.")

        self.task_type_1.refresh_from_db()
        self.assertEqual(self.task_type_1.name, "Updated Task Type")
        self.assertEqual(self.task_type_1.definition, "Updated definition.")

    def test_delete_task_type(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(TaskType.objects.filter(id=self.task_type_1.id).exists())

    def test_update_duplicate_name_in_same_project(self):
        data = {
            "name": "Schedule Appointment",
        }
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "A task type with name 'Schedule Appointment' already exists in this project.",
            response.data["name"],
        )

    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
