import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.insight import Insight
from api.models.note import Note
from api.models.project import Project
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.user import User
from api.models.workspace import Workspace
from api.serializers.tag import TagSerializer


# Create your tests here.
class TestInsightTagView(APITestCase):
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
        self.project = Project.objects.create(name="project", workspace=self.workspace)
        self.insight = Insight.objects.create(
            title="insight", project=self.project, created_by=self.user
        )
        self.project.users.add(self.user)

        self.note = Note.objects.create(
            title="note", project=self.project, author=self.user
        )
        self.takeaway1 = Takeaway.objects.create(
            title="takeaway 1 in insight", note=self.note, created_by=self.user
        )
        self.tag1 = Tag.objects.create(name="tag 1 in takeaway 1", project=self.project)
        self.tag2 = Tag.objects.create(name="tag 2 in takeaway 1", project=self.project)
        self.takeaway1.tags.add(self.tag1)
        self.takeaway1.tags.add(self.tag2)
        self.insight.takeaways.add(self.takeaway1)

        self.takeaway2 = Takeaway.objects.create(
            title="takeaway 2", note=self.note, created_by=self.user
        )
        self.tag3 = Tag.objects.create(name="tag 3 in takeaway 2", project=self.project)
        self.takeaway2.tags.add(self.tag3)

        # Update tag.takeaway_count
        self.tag1.refresh_from_db()
        self.tag2.refresh_from_db()
        self.tag3.refresh_from_db()

        self.url = f"/api/insights/{self.insight.id}/tags/"
        return super().setUp()

    def test_user_list_insight_tags(self):
        expected_result = TagSerializer([self.tag1, self.tag2], many=True).data

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_result)

    def test_outsider_list_insight_tags(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
