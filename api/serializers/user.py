# user/serializers.py
from rest_framework import serializers

from api.models.user import User
from api.models.workspace_user import WorkspaceUser


# User serializer class as nested field in other serializer class
class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]


class ProjectUserListSerializer(UserSerializer):
    role = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "role"]


class UsernameSerializer(serializers.ModelSerializer):
    username = serializers.EmailField()

    class Meta:
        model = User
        fields = ["username"]


class ProjectUserDeleteSerializer(serializers.Serializer):
    users = UsernameSerializer(many=True)


class WorkspaceUserSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    username = serializers.EmailField(write_only=True)

    class Meta:
        model = WorkspaceUser
        fields = ["user", "role", "username"]

    def validate_role(self, value):
        if value == WorkspaceUser.Role.OWNER:
            raise serializers.ValidationError("Cannot assign owner role to a user")
        return value

    def update(self, instance, validated_data):
        if instance.workspace.owned_by == instance.user:
            raise serializers.ValidationError(
                {"username": ["You cannot change the role of the workspace owner"]}
            )

        # username is used only to get the instance in the view
        # and is not to be updated
        validated_data.pop("username")
        return super().update(instance, validated_data)
