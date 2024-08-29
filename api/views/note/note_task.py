from rest_framework import generics

from api.filters.task import TaskFilter
from api.models.task import Task
from api.serializers.task import TaskSerializer


class NoteTaskListCreateView(generics.ListCreateAPIView):
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
        return self.request.note.tasks.all()
