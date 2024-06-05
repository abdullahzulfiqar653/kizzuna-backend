import logging

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.option import Option
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace
from api.views.property.property import increment_copy_number


# Create your tests here.
class TestPropertyRetrieveUpdateDestroyAPIView(APITestCase):
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
            name="property 1", data_type="MultiSelect"
        )
        self.option1 = self.property.options.create(name="option 1")
        self.option2 = self.property.options.create(name="option 2")

    def test_user_update_property(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/properties/{self.property.id}/",
            data={"name": "updated property 1"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.property.refresh_from_db()
        self.assertEqual(self.property.name, "updated property 1")

    def test_user_delete_property(self):
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/properties/{self.property.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.project.properties.count(), 0)

    def test_outsider_update_property(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.patch(
            f"/api/properties/{self.property.id}/",
            data={"name": "updated property 1"},
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# Create your tests here.
class TestPropertyDuplicateAPIView(APITestCase):
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
            name="property 1", data_type="MultiSelect"
        )
        self.option1 = self.property.options.create(name="option 1")
        self.option2 = self.property.options.create(name="option 2")

    def test_user_duplicate_property(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(f"/api/properties/{self.property.id}/duplicate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.project.properties.count(), 2)
        duplicated_property = self.project.properties.exclude(
            id=self.property.id
        ).first()
        self.assertEqual(duplicated_property.name, "property 1 copy")
        self.assertEqual(duplicated_property.options.count(), 2)
        self.assertEqual(duplicated_property.options.first().name, "option 1")
        self.assertEqual(duplicated_property.options.last().name, "option 2")
        # Make sure that the options are duplicated
        self.assertEqual(Option.objects.count(), 4)

    def test_increment_copy_number_function(self):
        name = "original name"
        existing_names = ["original name"]
        expected_name_copies = [
            "original name copy",
            "original name copy 2",
            "original name copy 3",
        ]

        for copy in expected_name_copies:
            name = increment_copy_number(name, existing_names)
            self.assertEqual(name, copy)
            existing_names.append(name)
