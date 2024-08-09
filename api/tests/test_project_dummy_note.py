import logging

import numpy as np
from rest_framework.test import APITestCase

from api.models.note_type import NoteType
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.user import User
from api.models.workspace import Workspace


class TestProjectDummyNoteCreateView(APITestCase):
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

        self.note_type = NoteType.objects.create(
            name="User Interview", project=self.project, vector=np.random.rand(1536)
        )
        return super().setUp()

    def test_user_create_dummy_note(self):
        """
        Test if the user can create a dummy note.
        """
        self.client.force_authenticate(self.user)
        response = self.client.post(f"/api/projects/{self.project.id}/dummy-reports/")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.project.notes.count(), 2)
        self.assertEqual(Takeaway.objects.count(), 35)
