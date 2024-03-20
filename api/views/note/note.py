from django.db.models import Count
from rest_framework import generics

from api.models.note import Note
from api.serializers.note import NoteSerializer, NoteUpdateSerializer


class NoteRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    def get_serializer_class(self):
        match self.request.method:
            case "PUT":
                return NoteUpdateSerializer
            case "PATCH":
                return NoteUpdateSerializer
            case _:
                return NoteSerializer

    def get_queryset(self):
        return Note.objects.annotate(takeaway_count=Count("takeaways"))
