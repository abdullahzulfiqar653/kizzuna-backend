# user/serializers.py
from rest_framework import serializers

from api.models.user import User


# User serializer class as nested field in other serializer class
class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]
