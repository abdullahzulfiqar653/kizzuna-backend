# user/serializers.py
from rest_framework import serializers

from api.models.user import User
from api.serializers.workspace import WorkspaceSerializer


# User serializer class for updating the user profile data
class UserProfileUpdateSerializer(serializers.ModelSerializer):
    workspaces = WorkspaceSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "workspaces", "skip_tutorial"]

    def validate_email(self, value):
        if not value:
            return value

        if value == self.context["request"].user.email:
            return value

        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                f"Email {value} is already used in another account."
            )

        return value

    def update(self, instance, validated_data):
        if "email" in validated_data:
            validated_data["username"] = validated_data["email"]
        # TODO: Update user object also
        return super().update(instance, validated_data)
