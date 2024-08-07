from rest_framework import generics
from api.models.playbook import PlayBook
from api.serializers.playbook import PlayBookSerializer


class PlaybookRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PlayBook.objects.all()
    serializer_class = PlayBookSerializer

    def get_queryset(self):
        return self.request.playbook.project.workspace.playbooks.all()
