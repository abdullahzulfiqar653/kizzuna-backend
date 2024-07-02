from rest_framework import generics

from api.models.message import Message
from api.serializers.message import MessageSerializer


class NoteMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    queryset = Message.objects.all()
    ordering = ["order"]
