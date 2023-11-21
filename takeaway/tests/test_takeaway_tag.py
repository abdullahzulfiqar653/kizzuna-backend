import logging

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from note.models import Note
from project.models import Project
from tag.models import Tag
from takeaway.models import Insight, Takeaway
from workspace.models import Workspace


# Create your tests here.
class TestTakeawayTagView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username="user", password="password")
        self.outsider = User.objects.create_user(
            username="outsider", password="password"
        )

        self.workspace = Workspace.objects.create(name="workspace")
        self.project = Project.objects.create(name="project", workspace=self.workspace)
        self.insight = Insight.objects.create(
            title="insight", project=self.project, created_by=self.user
        )
        self.project.users.add(self.user)

        self.note = Note.objects.create(
            title="note", project=self.project, author=self.user
        )
        self.takeaway1 = Takeaway.objects.create(
            title="takeaway 1", note=self.note, created_by=self.user
        )
        self.takeaway2 = Takeaway.objects.create(
            title="takeaway 2", note=self.note, created_by=self.user
        )
        self.tag = Tag.objects.create(name="tag", project=self.project)
        self.takeaway1.tags.add(self.tag)

        self.url1 = f"/api/takeaways/{self.takeaway1.id}/tags/"
        self.url2 = f"/api/takeaways/{self.takeaway2.id}/tags/"
        return super().setUp()

    def test_user_create_takeaway_tags_with_new_tag(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url1, data={"name": "new tag"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(name="new tag", project=self.project)
        self.assertEqual(new_tag.takeaway_count, 1)

    def test_user_create_takeaway_tags_with_existing_tag(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url2, data={"name": "tag"})
        self.tag.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.tag.takeaway_count, 2)

    def test_user_delete_takeaway_tags_with_no_remaining_takeaways(self):
        self.client.force_authenticate(self.user)
        url = f"{self.url1}{self.tag.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.contains(self.tag))

    def test_user_delete_takeaway_tags_with_remaining_takeaways(self):
        self.takeaway2.tags.add(self.tag)
        self.client.force_authenticate(self.user)
        url = f"{self.url1}{self.tag.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Tag.objects.contains(self.tag))
        self.tag.refresh_from_db()
        self.assertEqual(self.tag.takeaway_count, 1)
