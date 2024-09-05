from rest_framework import generics

from api.models.task_type import TaskType
from api.serializers.task_type import TaskTypeSerializer


class TaskTypeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskTypeSerializer
    queryset = TaskType.objects.all()
    ordering = ["-created_at", "name"]
    ordering_fields = ["created_at", "name"]
    search_fields = ["name"]
