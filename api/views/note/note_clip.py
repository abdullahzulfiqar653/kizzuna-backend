from rest_framework import generics

from api.serializers.note_clip import NoteClipCreateSerializer


class NoteClipCreateView(generics.CreateAPIView):
    serializer_class = NoteClipCreateSerializer
