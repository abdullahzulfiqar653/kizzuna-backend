# user/serializers.py
from rest_framework import serializers

from user.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']

    def create(self, validated_data):
        
        user = User(
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name')
        )
        user.save()

        return user