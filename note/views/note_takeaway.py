from django.shortcuts import get_object_or_404
from rest_framework import exceptions, generics

from note.models import Note
from takeaway.models import Takeaway
from takeaway.serializers import TakeawaySerializer


class NoteTakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer
    ordering_fields = [
        "created_at",
        "created_by__first_name",
        "created_by__last_name",
        "title",
    ]
    ordering = ["created_at"]
    search_fields = [
        "title",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]

    def get_queryset(self):
        auth_user = self.request.user
        note_id = self.kwargs.get("report_id")
        note = get_object_or_404(Note, id=note_id)
        if not note.project.users.contains(auth_user):
            raise exceptions.PermissionDenied
        return Takeaway.objects.filter(note=note)

    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(request.user):
            raise exceptions.PermissionDenied
        request.data["note"] = note.id
        return super().create(request)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
