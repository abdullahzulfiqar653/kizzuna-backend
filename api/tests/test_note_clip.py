import io
import json
import logging

from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.feature import Feature
from api.models.highlight import Highlight
from api.models.note import Note
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


class TestNoteClipCreateView(APITestCase):
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

        with open("api/tests/files/sample-transcript.json", "r") as file:
            transcript = json.load(file)

        with open("api/tests/files/sample-audio.mp3", "rb") as file:
            file_content = ContentFile(io.BytesIO(file.read()).read(), "test.mp3")
            self.note = Note.objects.create(
                title="Sample note",
                project=self.project,
                author=self.user,
                file=file_content,
                file_size=1073739824,  # 1.99GB
                transcript=transcript,  # Mock transcript
            )
        self.note.workspace = workspace
        self.note.save()
        Feature.objects.filter(code=Feature.Code.STORAGE_GB_WORKSPACE).update(default=1)
        self.url = f"/api/reports/{self.note.id}/clips/"

        return super().setUp()

    def test_create_highlight_success(self):
        data = {
            "start": 240,  # in ms
            "end": 456,  # in ms
        }
        expected_highlight_title = "Okay,"

        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        highlight = Highlight.objects.first()
        self.assertIsNotNone(highlight)
        self.assertEqual(highlight.title, expected_highlight_title)
        # Make sure that the clip is actually created
        self.assertTrue(highlight.clip.size > 0)
        # Clean up the clip file
        highlight.delete()

    def test_create_highlight_exceeds_duration(self):
        data = {
            "start": 0,
            "end": 310000,  # 310000 ms = 5 min 10 sec, exceeds 5 min limit
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(
            "You cannot make a clip greater than 5 minutes.", response.data["detail"]
        )

    def test_create_highlight_exceeds_storage_limit(self):
        data = {
            "start": 240,  # in ms
            "end": 3710,  # in ms
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You have reached the storage limit", response.data["detail"])

    def test_create_highlight_no_permission(self):
        data = {
            "start": 0,
            "end": 10000,
        }
        self.client.force_authenticate(None)  # No user authenticated
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_highlight_invalid_time(self):
        data = {
            "start": 10000,
            "end": 5000,  # End time is before start time
        }
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("End time must be after start time.", response.data["end"])
