import logging

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from project.models import Project
from takeaway.models import Insight
from workspace.models import Workspace


# Create your tests here.
class TestInsightRetrieveUpdateDeleteView(APITestCase):
    def setUp(self) -> None:
        """Reduce the log level to avoid errors like 'not found'"""
        logger = logging.getLogger("django.request")
        self.previous_level = logger.getEffectiveLevel()
        logger.setLevel(logging.ERROR)

        self.user = User.objects.create_user(username='user', password='password')
        self.outsider = User.objects.create_user(username='outsider', password='password')

        workspace = Workspace.objects.create(name='workspace')
        self.project = Project.objects.create(name='project', workspace=workspace)
        self.insight = Insight.objects.create(title='insight', project=self.project, created_by=self.user)
        self.project.users.add(self.user)

        self.url = f'/api/insights/{self.insight.id}/'
        return super().setUp()

    def test_user_retrieve_insight_details(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'insight')

    def test_user_delete_insight_details(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_retrieve_insight_details(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_delete_insight_details(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
