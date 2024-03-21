import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestSavedTakeawayView(APITestCase):
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
        self.user.saved_takeaways.add(self.takeaway1)

        return super().setUp()

    def test_user_list_saved_takeaways(self):
        url = "/api/saved/takeaways/"
        self.client.force_authenticate(self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_takeaway_ids = [takeaway["id"] for takeaway in response.json()]
        self.assertCountEqual(response_takeaway_ids, [self.takeaway1.id])

    def test_user_list_saved_takeaways_in_another_project(self):
        """
        If the user saved the takeaway, but later get removed from the project,
        we will keep the saved takeaway, but will not show it
        when we are listing the saved takeaways.
        """
        url = "/api/saved/takeaways/"
        self.client.force_authenticate(self.user)
        self.takeaway1.note.project.users.remove(self.user)
        self.takeaway1.note.save()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_takeaway_ids = [takeaway["id"] for takeaway in response.json()]
        # Assert that the saved takeaway is still exists in database
        self.assertTrue(self.user.saved_takeaways.filter(id=self.takeaway1.id).exists())
        # Assert that it is not shown in the response
        self.assertCountEqual(response_takeaway_ids, [])

    def test_user_create_saved_takeaways(self):
        # Assert that takeaway2 is not in the original saved takeaways
        takeaway_ids = [takeaway.id for takeaway in self.user.saved_takeaways.all()]
        self.assertCountEqual(takeaway_ids, [self.takeaway1.id])

        url = "/api/saved/takeaways/"
        self.client.force_authenticate(self.user)
        data = {
            "takeaways": [
                {
                    "id": self.takeaway2.id,
                },
            ]
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert that takeaway2 is added to the saved takeaways
        takeaway_ids = [takeaway.id for takeaway in self.user.saved_takeaways.all()]
        self.assertCountEqual(takeaway_ids, [self.takeaway1.id, self.takeaway2.id])

    def test_user_delete_saved_takeaways(self):
        # Assert that takeaway1 is in the original saved takeaways
        takeaway_ids = [takeaway.id for takeaway in self.user.saved_takeaways.all()]
        self.assertCountEqual(takeaway_ids, [self.takeaway1.id])

        url = "/api/saved/takeaways/delete/"
        self.client.force_authenticate(self.user)
        data = {
            "takeaways": [
                {
                    "id": self.takeaway1.id,
                },
            ]
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that takeaway1 is deleted from the saved takeaways
        takeaway_ids = [takeaway.id for takeaway in self.user.saved_takeaways.all()]
        self.assertCountEqual(takeaway_ids, [])

        # Assert that only the saved takeaway is removed, takeaway1 still exists
        self.assertTrue(Takeaway.objects.filter(id=self.takeaway1.id).exists())

    def test_outsider_create_saved_takeaways(self):
        url = "/api/saved/takeaways/"
        self.client.force_authenticate(self.outsider)
        data = {
            "takeaways": [
                {
                    "id": self.takeaway1.id,
                },
            ]
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
