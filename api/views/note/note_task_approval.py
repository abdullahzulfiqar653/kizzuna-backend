from rest_framework import generics
from api.serializers.task_approval import TaskApprovalSerializer


class NoteTaskApprovalCreateView(generics.CreateAPIView):
    serializer_class = TaskApprovalSerializer
