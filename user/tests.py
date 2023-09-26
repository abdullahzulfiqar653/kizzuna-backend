from django.test import TestCase
from user.serializers import UserSerializer
from user.models import User

class UserSerializerTestCase(TestCase):

    def setUp(self):
        self.user_attributes = {
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        self.serializer_data = UserSerializer().data
        self.user = User.objects.create(**self.user_attributes)

    def test_contains_expected_fields(self):
        serializer_data = UserSerializer(instance=self.user).data
        self.assertCountEqual(serializer_data.keys(), ['first_name', 'last_name'])

    def test_valid_serializer(self):
        serializer = UserSerializer(data=self.user_attributes)
        self.assertTrue(serializer.is_valid())

    def test_invalid_serializer(self):
        serializer = UserSerializer(data={'first_name': 'John'})
        self.assertFalse(serializer.is_valid())

    def test_serializer_create(self):
        serializer = UserSerializer(data=self.user_attributes)
        if serializer.is_valid():
            user = serializer.save()
            self.assertEqual(user.first_name, self.user_attributes['first_name'])
            self.assertEqual(user.last_name, self.user_attributes['last_name'])