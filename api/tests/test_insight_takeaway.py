import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.insight import Insight
from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.user import User
from api.models.workspace import Workspace
from api.serializers.takeaway import TakeawaySerializer


# Create your tests here.
class TestInsightTakeawayView(APITestCase):
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

        self.takeaway_in_insight = Takeaway.objects.create(
            title="takeaway in insight", note=self.note, created_by=self.user
        )
        self.insight.takeaways.add(self.takeaway_in_insight)

        self.url = f"/api/insights/{self.insight.id}/takeaways/"
        self.delete_url = f"/api/insights/{self.insight.id}/takeaways/delete/"
        return super().setUp()

    def test_user_list_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        expected_result = TakeawaySerializer(
            self.insight.takeaways.all(), many=True
        ).data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_result)

    def test_user_create_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        data = {
            "takeaways": [
                {
                    "id": self.takeaway1.id,
                },
                {
                    "id": self.takeaway2.id,
                },
            ]
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(self.insight.takeaways.contains(self.takeaway1))
        self.assertTrue(self.insight.takeaways.contains(self.takeaway2))

    def test_user_create_nonproject_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        other_project = Project.objects.create(
            name="other project", workspace=self.workspace
        )
        other_project_note = Note.objects.create(
            title="other project note", project=other_project, author=self.user
        )
        other_project_takeaway = Takeaway.objects.create(
            title="other project takeaway",
            note=other_project_note,
            created_by=self.user,
        )
        data = {
            "takeaways": [
                {
                    "id": other_project_takeaway.id,
                },
            ]
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_delete_insight_takeaways(self):
        self.client.force_authenticate(self.user)
        data = {
            "takeaways": [
                {
                    "id": self.takeaway_in_insight.id,
                },
            ]
        }
        response = self.client.post(self.delete_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.insight.takeaways.contains(self.takeaway_in_insight))

    def test_outsider_list_insight_takeaways(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_create_insight_takeaways(self):
        self.client.force_authenticate(self.outsider)
        data = {
            "takeaways": [
                {
                    "id": self.takeaway1.id,
                },
                {
                    "id": self.takeaway2.id,
                },
            ]
        }
        response = self.client.post(self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_delete_insight_takeaways(self):
        self.client.force_authenticate(self.outsider)
        data = {
            "takeaways": [
                {
                    "id": self.takeaway_in_insight.id,
                },
            ]
        }
        response = self.client.post(self.delete_url, data=data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
