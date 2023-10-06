# workspace/serializers.py
from rest_framework import serializers

from .models import Workspace

class WorkspaceSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=100)

    class Meta:
        model = Workspace
        fields = ['id', 'name']

    def validate_name(self, value):
        name = value
        if name and Workspace.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError(f"Workspace Name {name} already taken.")
        return value

    def create(self, validated_data):

        workspace = Workspace(
            name=validated_data.get('name')
        )
        workspace.save()

        request = self.context['request']
        request.user.workspaces.add(workspace)

        return workspace