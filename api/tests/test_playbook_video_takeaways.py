import io
import logging

import numpy as np
from django.conf import settings
from django.core.files.base import ContentFile
from pydub.utils import mediainfo
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.highlight import Highlight
from api.models.note import Note
from api.models.playbook import Playbook
from api.models.playbook_takeaway import PlaybookTakeaway
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestPlaybookVideoTakeawaysListCreateView(APITestCase):
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

        self.url = f"/api/playbooks/{self.playbook.id}/video/takeaways/"

        return super().setUp()

    def test_list_playbook_takeaways(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["takeaway"]["id"], self.takeaway_1.id)

    def test_create_playbook_takeaway_success(self):
        data = {"takeaway_id": self.takeaway_2.id, "order": 2}
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PlaybookTakeaway.objects.count(), 2)
        playbook_takeaway = PlaybookTakeaway.objects.latest("id")
        self.assertEqual(playbook_takeaway.takeaway_id, self.takeaway_2.id)
        self.assertEqual(playbook_takeaway.order, 2)

        # Check that the duration is correct
        path = (
            playbook_takeaway.takeaway.highlight.clip.url
            if settings.USE_S3
            else playbook_takeaway.takeaway.highlight.clip.path
        )
        audio_info = mediainfo(path)
        duration_in_seconds = float(audio_info.get("duration"))
        expected_duration = 0.677
        self.assertAlmostEqual(duration_in_seconds, expected_duration, places=2)

    def test_create_playbook_takeaway_from_private_note(self):
        """
        Test that a user cannot add a takeaway from a private note to a playbook.
        """
        # Create a private note
        private_note = Note.objects.create(
            title="Private Note",
            project=self.project,
            author=self.outsider,
            is_shared=False,
        )
        # Add the takeaway to the private note
        takeaway = Highlight.objects.create(
            quote="This is a takeaway from a private note.",
            note=private_note,
            clip=self.takeaway_1.clip,
            created_by=self.outsider,
            vector=np.random.rand(1536),
        )
        data = {"takeaway_id": takeaway.id, "order": 1}
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_playbook_takeaway_order(self):
        data = {"takeaway_id": self.takeaway_2.id, "order": 2}
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["order"], 1)
        self.assertEqual(response.data[1]["order"], 2)
        self.assertEqual(response.data[0]["takeaway"]["id"], self.takeaway_1.id)
        self.assertEqual(response.data[1]["takeaway"]["id"], self.takeaway_2.id)

    def test_create_playbook_takeaway_already_exists(self):
        data = {"takeaway_id": self.takeaway_1.id, "order": 1}
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Takeaway already exists in playbook", response.data["takeaway_id"]
        )

    def test_create_playbook_takeaway_unauthenticated(self):
        data = {"takeaway_id": self.takeaway_1.id, "order": 2}
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_playbook_takeaway_invalid_takeaway(self):
        data = {"takeaway_id": 9999, "order": 2}
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_messages = response.data.get("takeaway_id", [])
        expected_error_message = 'Invalid pk "9999" - object does not exist.'
        self.assertIn(
            expected_error_message,
            error_messages,
            f"Expected error message '{expected_error_message}' for takeaway_id.",
        )
