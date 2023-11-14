import logging

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from note.models import Note
from project.models import Project
from tag.models import Keyword
from takeaway.models import Insight, Takeaway
from workspace.models import Workspace


# Create your tests here.
class TestNoteKeywordDestroyView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username='user', password='password')
        self.outsider = User.objects.create_user(username='outsider', password='password')

        workspace = Workspace.objects.create(name='workspace')
        self.project = Project.objects.create(name='project', workspace=workspace)
        self.project.users.add(self.user)

        self.note = Note.objects.create(title='note', project=self.project, author=self.user)
        self.existing_keyword = Keyword.objects.create(name='keyword')
        self.note.keywords.add(self.existing_keyword)
        return super().setUp()

    def test_user_create_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        keyword_id = self.existing_keyword.id
        url = f'/api/reports/{self.note.id}/keywords/{keyword_id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.note.keywords.contains(self.existing_keyword))

    def test_user_create_nonexisting_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        non_existing_keyword_id = 'nonexistenceid'
        url = f'/api/reports/{self.note.id}/keywords/{non_existing_keyword_id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_create_insight_takeaways(self):
        self.client.force_authenticate(self.outsider)
        keyword_id = self.existing_keyword.id
        url = f'/api/reports/{self.note.id}/keywords/{keyword_id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(self.note.keywords.contains(self.existing_keyword))
