from rest_framework import generics

from api.serializers.task import TaskSerializer


class NoteTaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
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
