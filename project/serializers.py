# api/serializers.py
from rest_framework import serializers
from project.models import Project

class ProjectSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'status']

    def __init__(self, *args, **kwargs):
        request = kwargs.get('context', {}).get('request')
        if request is not None and hasattr(request, 'user'):
            self.user = request.user
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        auth_user = self.user
        workspace = auth_user.workspaces.first()
        validated_data['workspace'] = workspace
        validated_data['users'] = [auth_user]
        return super().create(validated_data)
