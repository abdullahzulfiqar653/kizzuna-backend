import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestPropertyOptionListCreateView(APITestCase):
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

    def test_user_list_property_options(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/properties/{self.property.id}/options/")
        self.assertEqual(response.status_code, 200)

        expected_result = [
            {
                "id": self.option.id,
                "order": 0,
                "name": "option 1",
                "created_at": self.option.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "updated_at": self.option.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "property": self.property.id,
            }
        ]
        self.assertCountEqual(response.json(), expected_result)

    def test_user_create_property_option(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            f"/api/properties/{self.property.id}/options/",
            data={
                "name": "option 2",
            },
        )
        self.assertEqual(response.status_code, 201)

        self.assertEqual(self.property.options.count(), 2)
        self.assertEqual(self.property.options.last().name, "option 2")

    def test_outsider_list_property_options(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(f"/api/properties/{self.property.id}/options/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
