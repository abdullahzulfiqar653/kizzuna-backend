from rest_framework import generics
from api.models.task import Task
from api.filters.task import TaskFilter
from api.serializers.task import TaskSerializer


class ProjectTaskListView(generics.ListAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filterset_class = TaskFilter
    ordering_fields = [
        "created_at",
        "created_by__first_name",
        "created_by__last_name",
        "title",
    ]
    ordering = ["created_at"]
    search_fields = [
        "title",
        "status",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]

    def get_queryset(self):
        return Task.objects.filter(note__project=self.request.project)
