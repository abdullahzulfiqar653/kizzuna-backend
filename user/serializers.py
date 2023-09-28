# user/serializers.py
from django.contrib.auth.models import User as AuthUser
from rest_framework import serializers

from user.models import User
from workspace.serializers import WorkspaceSerializer


# AuthUser serializer class as nested field in other serializer class
class AuthUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = AuthUser
        fields = ['email', 'first_name', 'last_name']


# AuthUser serializer class for updating the user profile data
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    workspaces = WorkspaceSerializer(many=True, read_only=True)

    class Meta:
        model = AuthUser
        fields = ['email', 'first_name', 'last_name', 'workspaces']

    def validate_email(self, value):
        if not value:
            return value
        
        if value == self.context['request'].user.email:
            return value

        if value and AuthUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"Email {value} is already used in another account.")

        return value

    def update(self, instance, validated_data):
        if 'email' in validated_data:
            validated_data['username'] = validated_data['email']
        return super().update(instance, validated_data)

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