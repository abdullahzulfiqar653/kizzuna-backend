from rest_framework import generics
from api.serializers.playbook import PlayBookSerializer


class PlaybookRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PlayBookSerializer

    def get_queryset(self):
        return self.request.playbook.project.playbooks.prefetch_related(
            "takeaways"
        ).all()
