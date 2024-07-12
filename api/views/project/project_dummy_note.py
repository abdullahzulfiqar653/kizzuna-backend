from rest_framework import generics

from api.serializers.dummy_note import DummyNoteCreateSerializer


class ProjectDummyNoteCreateView(generics.CreateAPIView):
    serializer_class = DummyNoteCreateSerializer
