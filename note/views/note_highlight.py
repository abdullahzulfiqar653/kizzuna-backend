from rest_framework import generics

from takeaway.models import Highlight
from takeaway.serializers import HighlightSerializer


class NoteHighlightCreateView(generics.CreateAPIView):
    queryset = Highlight.objects.all()
    serializer_class = HighlightSerializer
