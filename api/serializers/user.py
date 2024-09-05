# user/serializers.py
from rest_framework import exceptions, serializers

from api.models import Feature, User, WorkspaceUser


# User serializer class as nested field in other serializer class
class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get("allow_email_write", False):
            self.fields["email"].read_only = False


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

        if validated_data["role"] == WorkspaceUser.Role.EDITOR:
            editors_limit = instance.workspace.get_feature_value(
                Feature.Code.NUMBER_OF_EDITORS
            )
            number_of_editors = instance.workspace.workspace_users.filter(
                role__in=[WorkspaceUser.Role.EDITOR, WorkspaceUser.Role.OWNER]
            ).count()
            if number_of_editors >= editors_limit:
                raise exceptions.PermissionDenied(
                    f"You have reached the limit of {editors_limit} Editors."
                )

        # username is used only to get the instance in the view
        # and is not to be updated
        validated_data.pop("username")
        return super().update(instance, validated_data)
