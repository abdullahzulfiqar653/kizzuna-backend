import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace
from api.serializers.property import find_unique_name


# Create your tests here.
class TestProjectPropertyListCreateView(APITestCase):
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

    def test_user_list_project_properties(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/projects/{self.project.id}/properties/")
        self.assertEqual(response.status_code, 200)

        expected_result = [
            {
                "id": self.property.id,
                "order": 0,
                "name": "property 1",
                "description": "",
                "data_type": "Select",
                "created_at": self.property.created_at.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "updated_at": self.property.updated_at.strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "project": self.project.id,
            }
        ]
        self.assertCountEqual(response.json(), expected_result)

    def test_user_create_project_property(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            f"/api/projects/{self.project.id}/properties/",
            data={
                "name": "number property",
                "description": "description",
                "data_type": "Number",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.project.properties.count(), 2)

    def test_outside_user_project_properties(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(f"/api/projects/{self.project.id}/properties/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_increment_copy_number_function(self):
        name = "Text"
        existing_names = ["Text"]
        expected_name_copies = [
            "Text 2",
            "Text 3",
        ]

        for copy in expected_name_copies:
            base_name = "Text"
            name = find_unique_name(base_name, existing_names)
            self.assertEqual(name, copy)
            existing_names.append(name)
