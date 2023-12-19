from django.contrib.auth.models import User as AuthUser
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from user.models import User
from user.serializers import UserSerializer


class UserSerializerTestCase(TestCase):
    def setUp(self):
        self.user_attributes = {"first_name": "John", "last_name": "Doe"}

        self.serializer_data = UserSerializer().data
        self.user = User.objects.create(**self.user_attributes)

    def test_contains_expected_fields(self):
        serializer_data = UserSerializer(instance=self.user).data
        self.assertCountEqual(serializer_data.keys(), ["first_name", "last_name"])

    def test_valid_serializer(self):
        serializer = UserSerializer(data=self.user_attributes)
        self.assertTrue(serializer.is_valid())

    def test_invalid_serializer(self):
        serializer = UserSerializer(data={"first_name": "John"})
        self.assertFalse(serializer.is_valid())

    def test_serializer_create(self):
        serializer = UserSerializer(data=self.user_attributes)
        if serializer.is_valid():
            user = serializer.save()
            self.assertEqual(user.first_name, self.user_attributes["first_name"])
            self.assertEqual(user.last_name, self.user_attributes["last_name"])


class TestAuthUserRetrieveUpdateDestroyView(APITestCase):
    def setUp(self) -> None:
        self.user = AuthUser.objects.create_user(username="user", password="password")
        self.outsider = AuthUser.objects.create_user(
            username="outsider", password="password"
        )
        self.user_count = AuthUser.objects.count()
        self.username_set = set(AuthUser.objects.values_list("username", flat=True))

    def test_user_update_email(self):
        self.client.force_authenticate(self.user)
        url = "/api/auth-users/"
        response = self.client.patch(url, data={"email": "user@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "user@example.com")

    def test_user_delete_account(self):
        self.client.force_authenticate(self.user)
        url = "/api/auth-users/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AuthUser.objects.count(), self.user_count - 1)
        self.assertSetEqual(
            set(AuthUser.objects.values_list("username", flat=True)),
            self.username_set - {"user"},
        )

    def test_outsider_delete_account(self):
        self.client.force_authenticate(self.outsider)
        url = "/api/auth-users/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AuthUser.objects.count(), self.user_count - 1)
        self.assertSetEqual(
            set(AuthUser.objects.values_list("username", flat=True)),
            self.username_set - {"outsider"},
        )
