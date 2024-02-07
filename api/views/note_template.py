from rest_framework import generics

from api.models.note_template import NoteTemplate
from api.serializers.note_template import NoteTemplateDetailSerializer


class NoteTemplateRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = NoteTemplate.objects.all()
    serializer_class = NoteTemplateDetailSerializer
