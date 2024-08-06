from rest_framework import generics
from api.serializers.note_highlight import NoteHighlightCreateSerializer


class NoteHighlightCreateView(generics.CreateAPIView):
    serializer_class = NoteHighlightCreateSerializer
