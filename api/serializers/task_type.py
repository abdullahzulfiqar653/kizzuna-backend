from rest_framework import serializers
from api.models.task_type import TaskType

class TaskTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType
        fields = [
            'id', 
            'name', 
            'definition',
            'created_at', 
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_name(self, value):
        project = self.context['request'].data.get('project')
        if TaskType.objects.filter(name=value, project=project).exists():
            raise serializers.ValidationError(f"A task type with name '{value}' already exists in this project.")
        return value
