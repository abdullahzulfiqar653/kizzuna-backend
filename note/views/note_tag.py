from rest_framework import exceptions, generics

from note.models.note import Note
from tag.models import Tag
from tag.serializers import TagSerializer


class NoteTagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    ordering = ["-takeaway_count", "name"]
    ordering_fields = ["created_at", "takeway_count", "name"]

    def get_queryset(self):
        report_id = self.kwargs["report_id"]
        note = Note.objects.filter(id=report_id).first()
        if note is None or not note.project.users.contains(self.request.user):
            raise exceptions.NotFound

        return Tag.objects.filter(takeaways__note=note).distinct()
