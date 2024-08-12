import json
import logging
from unittest.mock import MagicMock, patch

import numpy as np
from rest_framework.test import APITestCase

from api.ai.generators.tag_generator import generate_tags
from api.models.note import Note
from api.models.note_type import NoteType
from api.models.project import Project
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.models.workspace import Workspace


class TestNoteTagGenerateView(APITestCase):
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

        self.note_type1 = NoteType.objects.create(
            name="Report-type-1", project=self.project, vector=np.random.rand(1536)
        )
        self.note_type2 = NoteType.objects.create(
            name="Report-type-2", project=self.project, vector=np.random.rand(1536)
        )

        self.note = Note.objects.create(
            title="Sample report",
            project=self.project,
            author=self.user,
            type=self.note_type1,
        )
        self.takeaway_type1 = TakeawayType.objects.create(
            name="Takeaway-type-1", project=self.project
        )
        self.takeaway1 = self.note.takeaways.create(
            title="takeaway 1",
            created_by=self.user,
            vector=np.random.rand(1536),
            type=self.takeaway_type1,
        )
        self.takeaway2 = self.note.takeaways.create(
            title="takeaway 1",
            created_by=self.user,
            vector=np.random.rand(1536),
            type=self.takeaway_type1,
        )
        return super().setUp()

    @patch("langchain_core.runnables.base.RunnableSequence.invoke")
    def test_generate_tag(self, mocked_invoke: MagicMock):
        class MockedTakeawayListSchema:
            def dict():
                return {
                    "takeaways": [
                        {
                            "id": self.takeaway1.id,
                            "tags": [
                                "takeaway1 - tag1",
                                "takeaway1 - tag2",
                            ],
                        },
                        {
                            "id": self.takeaway2.id,
                            "tags": [
                                "takeaway2 - tag1",
                                "takeaway2 - tag2",
                            ],
                        },
                    ],
                }

        mocked_invoke.return_value = MockedTakeawayListSchema

        generate_tags(self.note, self.project.takeaway_types.all(), self.user)

        mocked_invoke.assert_called_once()
        invoked_data = json.loads(mocked_invoke.call_args[0][0]["takeaways"])[
            "takeaways"
        ]
        self.assertCountEqual(
            invoked_data,
            [
                {
                    "id": self.takeaway1.id,
                    "message": self.takeaway1.title,
                },
                {
                    "id": self.takeaway2.id,
                    "message": self.takeaway2.title,
                },
            ],
        )

        self.takeaway1.refresh_from_db()
        self.assertCountEqual(
            self.takeaway1.tags.values_list("name", flat=True),
            ["takeaway1 - tag1", "takeaway1 - tag2"],
        )
        self.assertCountEqual(
            self.takeaway2.tags.values_list("name", flat=True),
            ["takeaway2 - tag1", "takeaway2 - tag2"],
        )
