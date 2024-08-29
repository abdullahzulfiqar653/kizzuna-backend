from rest_framework import generics

from api.serializers.integrations.recall.bot import RecallBotSerializer


class ProjectRecallBotCreateView(generics.CreateAPIView):
    serializer_class = RecallBotSerializer
