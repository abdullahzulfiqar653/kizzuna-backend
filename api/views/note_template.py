from rest_framework import generics

from api.models.note_template import NoteTemplate
from api.permissions import (
    IsWorkspaceEditor,
    IsWorkspaceMemberReadOnly,
    PublicNoteTemplateReadOnly,
)
from api.serializers.note_template import NoteTemplateDetailSerializer


class NoteTemplateRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = NoteTemplate.objects.all()
    serializer_class = NoteTemplateDetailSerializer
    permission_classes = [
        IsWorkspaceEditor | IsWorkspaceMemberReadOnly | PublicNoteTemplateReadOnly
    ]
