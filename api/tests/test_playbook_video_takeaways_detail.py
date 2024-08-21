import io
import logging
import numpy as np
from rest_framework.test import APITestCase
from api.models.playbook import Playbook
from api.models.highlight import Highlight

from api.models.user import User
from api.models.workspace import Workspace
from api.models.project import Project
from api.models.note import Note
from django.core.files.base import ContentFile
from rest_framework import status
from api.models.playbook_takeaway import PlaybookTakeaway


class TestPlaybookVideoTakeawaysUpdateDeleteView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )
        self.workspace = Workspace.objects.create(name="workspace", owned_by=self.user)
        self.workspace.members.add(self.user, through_defaults={"role": "Editor"})
        self.project = Project.objects.create(name="project", workspace=self.workspace)
        self.project.users.add(self.user)

        self.note = Note.objects.create(
            title="Sample Note", project=self.project, author=self.user
        )

        with open("api/tests/files/test_takeaway_1.mp4", "rb") as file:
            file_content = ContentFile(io.BytesIO(file.read()).read(), "t_1.mp4")
        self.takeaway_1 = Highlight.objects.create(
            quote="This is abdullah.",
            note=self.note,
            clip=file_content,
            created_by=self.user,
            vector=np.random.rand(1536),
        )
        with open("api/tests/files/test_takeaway_2.mp4", "rb") as file:
            file_content = ContentFile(io.BytesIO(file.read()).read(), "t_2.mp4")
        self.takeaway_2 = Highlight.objects.create(
            quote="I am working on.",
            note=self.note,
            clip=file_content,
            created_by=self.user,
            vector=np.random.rand(1536),
        )

        self.playbook = Playbook.objects.create(
            title="Sample Playbook", created_by=self.user, project=self.project
        )
        self.playbook.notes.add(self.note)

        self.playbook_takeaway = PlaybookTakeaway.objects.create(
            playbook=self.playbook, takeaway=self.takeaway_1, order=1
        )

        self.url_update_delete = (
            lambda takeaway_id: f"/api/playbooks/{self.playbook.id}/video/takeaways/{takeaway_id}/"
        )
        return super().setUp()

    def test_update_playbook_takeaway(self):
        data = {"order": 3}
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            self.url_update_delete(self.takeaway_1.id), data=data, format="json"
        )
        updated_takeaway = PlaybookTakeaway.objects.get(id=response.data["id"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["order"], 3)
        self.assertEqual(updated_takeaway.order, 3)

    def test_update_playbook_takeaway_unauthenticated(self):
        data = {"order": 4}
        response = self.client.patch(
            self.url_update_delete(self.takeaway_1.id), data=data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_playbook_takeaway(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url_update_delete(self.takeaway_1.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            PlaybookTakeaway.objects.filter(id=self.playbook_takeaway.id).exists()
        )

    def test_delete_playbook_takeaway_unauthenticated(self):
        response = self.client.delete(self.url_update_delete(self.takeaway_2.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_playbook_takeaway_not_found(self):
        data = {"order": 5}
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            self.url_update_delete(9999), data=data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_playbook_takeaway_not_associated(self):
        another_playbook = Playbook.objects.create(
            title="Another Playbook", created_by=self.user, project=self.project
        )
        another_takeaway = PlaybookTakeaway.objects.create(
            playbook=another_playbook, takeaway=self.takeaway_2, order=1
        )
        self.client.force_authenticate(self.user)
        response = self.client.delete(
            self.url_update_delete(another_takeaway.takeaway.id)
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
