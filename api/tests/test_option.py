import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestOptionDestroyView(APITestCase):
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
        self.property = self.project.properties.create(
            name="property 1", data_type="Select"
        )
        self.option = self.property.options.create(name="option 1")

    def test_user_delete_option(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/options/{self.option.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(self.property.options.count(), 0)

    def test_outsider_delete_option(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.delete(f"/api/options/{self.option.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(self.property.options.count(), 1)
