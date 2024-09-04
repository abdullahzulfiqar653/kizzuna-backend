import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.playbook import Playbook
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestPlaybookRetrieveUpdateDeleteView(APITestCase):
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
        self.project = Project.objects.create(name="project", workspace=workspace)
        self.project.users.add(self.user)

        self.note = Note.objects.create(
            title="Sample note",
            project=self.project,
            author=self.user,
        )

        self.playbook = Playbook.objects.create(
            title="Sample Playbook",
            description="Description of the sample playbook",
            project=self.project,
            created_by=self.user,
        )

        self.url = f"/api/playbooks/{self.playbook.id}/"
        self.another_workspace = Workspace.objects.create(
            name="another_workspace", owned_by=self.outsider
        )
        self.another_project = Project.objects.create(
            name="another_project", workspace=self.another_workspace
        )
        self.another_project.users.add(self.outsider)

        return super().setUp()

    def test_retrieve_playbook_success(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.playbook.title)
        self.assertEqual(response.data["description"], self.playbook.description)

    def test_update_playbook_success(self):
        data = {
            "title": "Updated Playbook Title",
            "description": "Updated description",
            "report_ids": [self.note.id],
        }
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        playbook = Playbook.objects.get(id=self.playbook.id)
        self.assertEqual(playbook.title, data["title"])
        self.assertEqual(playbook.description, data["description"])
        self.assertEqual(playbook.notes.count(), 1)
        self.assertEqual(playbook.notes.first(), self.note)

    def test_update_playbook_with_private_note(self):
        """
        Test that a private note cannot be added to a playbook
        even if the user is the author
        """
        private_note = Note.objects.create(
            title="Private note",
            project=self.project,
            author=self.user,
            is_shared=False,
        )
        data = {
            "report_ids": [private_note.id],
        }
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_playbook_title_exists(self):
        Playbook.objects.create(
            title="Existing Playbook Title",
            description="Description of an existing playbook",
            project=self.project,
            created_by=self.user,
        )
        data = {
            "title": "Existing Playbook Title",
            "description": "Trying to update to an existing title",
        }
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], data["title"])

    def test_update_playbook_invalid_report_id(self):
        data = {
            "title": "Updated Playbook Title",
            "description": "Updated description",
            "report_ids": ["5FCrX2b9tzvu"],
        }
        self.client.force_authenticate(self.user)
        response = self.client.put(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            'Invalid pk "5FCrX2b9tzvu" - object does not exist.',
            response.data["report_ids"],
        )

    def test_delete_playbook_success(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Playbook.objects.filter(id=self.playbook.id).exists())

    def test_delete_playbook_no_permission(self):
        self.client.force_authenticate(None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Playbook.objects.filter(id=self.playbook.id).exists())

    def test_playbook_access_denied_to_user_from_another_project(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
