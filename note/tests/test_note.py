import logging

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from note.models import Note
from project.models import Project
from tag.models import Keyword
from takeaway.models import Highlight, Insight, Takeaway
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

    def test_user_delete_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        keyword_id = self.existing_keyword.id
        url = f'/api/reports/{self.note.id}/keywords/{keyword_id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(self.note.keywords.contains(self.existing_keyword))

    def test_user_delete_nonexisting_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        non_existing_keyword_id = 'nonexistenceid'
        url = f'/api/reports/{self.note.id}/keywords/{non_existing_keyword_id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_delete_insight_takeaways(self):
        self.client.force_authenticate(self.outsider)
        keyword_id = self.existing_keyword.id
        url = f'/api/reports/{self.note.id}/keywords/{keyword_id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(self.note.keywords.contains(self.existing_keyword))


class TestNoteUpdateView(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='user', password='password')

        workspace = Workspace.objects.create(name='workspace')
        self.project = Project.objects.create(name='project', workspace=workspace)
        self.project.users.add(self.user)

        self.note = Note.objects.create(
            title='note', 
            project=self.project, 
            author=self.user,
            content='This is a sample text only.',
        )
        self.highlight = Highlight.objects.create(
            start=10, 
            end=16, 
            note=self.note, 
            created_by=self.user,
        )
        return super().setUp()
    
    def test_highlight_remain_after_user_edit_note_content(self):
        self.client.force_authenticate(self.user)
        url = f'/api/reports/{self.note.id}/'
        data = {
            'content': 'This is an edited sample text.',
            'highlights': [
                {
                    'id': self.highlight.id,
                    'start': 18,
                    'end': 24,
                }
            ]
        }
        response = self.client.patch(url, data=data, format='json')
        self.highlight.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.note.highlights.contains(self.highlight))
        self.assertEqual(self.highlight.title, 'sample')
        self.assertEqual(self.highlight.start, 18)
        self.assertEqual(self.highlight.end, 24)
