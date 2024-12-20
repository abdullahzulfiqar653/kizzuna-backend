from django_celery_results.models import TaskResult
from rest_framework import serializers


class CeleryTaskResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskResult
        fields = "__all__"
