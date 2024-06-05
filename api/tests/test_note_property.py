import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.test import APITestCase

from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace


# Create your tests here.
class TestNotePropertyListView(APITestCase):
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
        self.text_property = self.project.properties.create(
            name="text property", data_type="Text"
        )
        self.number_property = self.project.properties.create(
            name="number property", data_type="Number"
        )
        self.select_property = self.project.properties.create(
            name="select property", data_type="Select"
        )

        self.option1 = self.select_property.options.create(name="option 1")
        self.option2 = self.select_property.options.create(name="option 2")

        self.note = self.project.notes.create(title="note 1", author=self.user)

    def test_user_list_note_properties(self):
        # The note properties should be created during list
        self.assertEqual(self.note.note_properties.count(), 0)

        self.client.force_authenticate(self.user)
        response = self.client.get(f"/api/reports/{self.note.id}/properties/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Make sure that the note properties are created during list
        self.assertEqual(self.note.note_properties.count(), 3)

    def test_outsider_list_note_properties(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(f"/api/reports/{self.note.id}/properties/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestNotePropertyUpdateView(APITestCase):
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
        self.property1 = self.project.properties.create(
            name="text property", data_type="Text"
        )
        self.property2 = self.project.properties.create(
            name="select property", data_type="Select"
        )

        self.option1 = self.property2.options.create(name="option 1")
        self.option2 = self.property2.options.create(name="option 2")

        self.note = self.project.notes.create(title="note 1", author=self.user)

    def test_user_update_note_properties(self):
        # The note properties should be created during update
        self.assertEqual(self.note.note_properties.count(), 0)

        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/reports/{self.note.id}/properties/{self.property1.id}/",
            data={
                "text_value": "value 1",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the text value is updated
        self.assertEqual(
            self.note.note_properties.get(property=self.property1).text_value, "value 1"
        )

    def test_user_update_note_number_properties(self):
        # The note properties should be created during update
        self.assertEqual(self.note.note_properties.count(), 0)

        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/reports/{self.note.id}/properties/{self.property1.id}/",
            data={
                "number_value": "100.010",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the number value is updated
        self.assertEqual(
            self.note.note_properties.get(property=self.property1).number_value,
            Decimal("100.010"),
        )
        # Check that the number value is returned with normalized precision
        self.assertEqual(response.json()["number_value"], "100.01")

    def test_user_update_note_properties_with_option(self):
        # The note properties should be created during update
        self.assertEqual(self.note.note_properties.count(), 0)

        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/reports/{self.note.id}/properties/{self.property2.id}/",
            data={
                "option_ids": [self.option1.id],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that the option is updated
        self.assertCountEqual(
            self.note.note_properties.get(property=self.property2).options.all(),
            [self.option1],
        )

    def test_user_update_note_properties_from_other_project(self):
        outsider_workspace = Workspace.objects.create(
            name="outsider workspace", owned_by=self.outsider
        )
        outsider_project = self.outsider.projects.create(
            name="outsider project", workspace=outsider_workspace
        )
        outsider_property = outsider_project.properties.create(name="outsider property")
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            f"/api/reports/{self.note.id}/properties/{outsider_property.id}/",
            data={
                "text_value": "value 1",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_outsider_update_note_properties(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.patch(
            f"/api/reports/{self.note.id}/properties/{self.property1.id}/",
            data={
                "text_value": "value 1",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
