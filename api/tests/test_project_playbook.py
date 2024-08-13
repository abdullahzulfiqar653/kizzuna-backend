import logging
from rest_framework import status
from rest_framework.test import APITestCase
from api.models.note import Note
from api.models.playbook import PlayBook
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectPlayBookListCreateView(APITestCase):
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

        self.url = f"/api/projects/{self.project.id}/playbooks/"

        return super().setUp()

    def test_create_playbook_success(self):
        data = {
            "title": "New Playbook",
            "description": "Description of the new playbook",
            "report_ids": [self.note.id],  # Assuming note IDs are valid for the test
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        playbook = PlayBook.objects.first()
        self.assertIsNotNone(playbook)
        self.assertEqual(playbook.title, data["title"])
        self.assertEqual(playbook.description, data["description"])
        self.assertEqual(playbook.notes.count(), 1)
        self.assertEqual(playbook.notes.first(), self.note)

    def test_create_playbook_no_permission(self):
        data = {
            "title": "Unauthorized Playbook",
            "description": "This should not be created",
        }
        self.client.force_authenticate(None)  # No user authenticated
        response = self.client.post(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_playbook_title_exists(self):
        PlayBook.objects.create(
            title="Existing Playbook",
            description="Existing playbook description",
            project=self.project,
            created_by=self.user,
            workspace=self.project.workspace
        )
        data = {
            "title": "Existing Playbook",
            "description": "This should raise an error",
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("A PlayBook with this title in the current project already exists.", response.data["title"])

    def test_list_playbooks_success(self):
        PlayBook.objects.create(
            title="First Playbook",
            description="Description of the first playbook",
            project=self.project,
            created_by=self.user,
            workspace=self.project.workspace
        )
        PlayBook.objects.create(
            title="Second Playbook",
            description="Description of the second playbook",
            project=self.project,
            created_by=self.user,
            workspace=self.project.workspace
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should list 2 playbooks
        self.assertEqual(response.data[1]["title"], "First Playbook")
        self.assertEqual(response.data[0]["title"], "Second Playbook")

    def test_list_playbooks_no_permission(self):
        self.client.force_authenticate(None)  # No user authenticated
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
