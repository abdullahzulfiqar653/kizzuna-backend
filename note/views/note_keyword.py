from django.shortcuts import get_object_or_404
from rest_framework import exceptions, generics, status
from rest_framework.response import Response

from note.models import Note
from tag.models import Keyword
from tag.serializers import KeywordSerializer


class NoteKeywordListCreateView(generics.ListCreateAPIView):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    ordering = ["title"]

    def get_queryset(self):
        auth_user = self.request.user
        note_id = self.kwargs.get("report_id")
        note = get_object_or_404(Note, id=note_id)
        if not note.project.users.contains(auth_user):
            raise exceptions.PermissionDenied
        return Keyword.objects.filter(note=note)

    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(request.user):
            raise exceptions.PermissionDenied
        request.data["note"] = note.id
        return super().create(request)

    def perform_create(self, serializer):
        report_id = self.kwargs.get("report_id")
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(self.request.user):
            raise exceptions.PermissionDenied
        keyword = serializer.save()
        note.keywords.add(keyword)


class NoteKeywordDestroyView(generics.DestroyAPIView):
    serializer_class = KeywordSerializer

    def destroy(self, request, report_id, keyword_id):
        note = Note.objects.filter(pk=report_id, project__users=request.user).first()
        if note is None:
            raise exceptions.NotFound(f"Report {report_id} not found.")

        keyword = note.keywords.filter(pk=keyword_id).first()
        if keyword is None:
            raise exceptions.NotFound(f"Keyword {keyword_id} not found.")

        note.keywords.remove(keyword)
        return Response(status=status.HTTP_204_NO_CONTENT)
