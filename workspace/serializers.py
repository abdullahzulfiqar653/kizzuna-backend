# workspace/serializers.py
from django.db.models import Q
from django.utils.text import slugify
from rest_framework import serializers

from .models import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=100)

    class Meta:
        model = Workspace
        fields = ['id', 'name']

    def validate_name(self, value):
        name = value
        slug = slugify(name)
        condition = Q(name__iexact=name) | Q(domain_slug=slug)
        if name and Workspace.objects.filter(condition).exists():
            raise serializers.ValidationError(f"Workspace Name already taken.")
        return value

    def create(self, validated_data):

        workspace = Workspace(
            name=validated_data.get('name')
        )
        workspace.save()

        request = self.context['request']
        request.user.workspaces.add(workspace)

        return workspace