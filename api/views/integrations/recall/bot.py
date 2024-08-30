from rest_framework import exceptions, generics, permissions

from api.integrations.recall import recall
from api.models.integrations.recall.bot import RecallBot
from api.serializers.integrations.recall.bot import RecallBotSerializer


class RecallBotDeleteView(generics.DestroyAPIView):
    serializer_class = RecallBotSerializer
    queryset = RecallBot.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, pk):
        recall_bot = RecallBot.objects.filter(pk=pk, created_by=request.user).first()
        if recall_bot is None:
            return exceptions.NotFound("Recall bot does not exist.")

        recall.v1.bot(recall_bot.id.hex).delete()
        return super().destroy(request, pk)
