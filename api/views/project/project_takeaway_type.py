from rest_framework import exceptions, generics

from api.models.takeaway_type import TakeawayType
from api.serializers.takeaway_type import TakeawayTypeSerializer


class ProjectTakeawayTypeListView(generics.ListAPIView):
    serializer_class = TakeawayTypeSerializer
    queryset = TakeawayType.objects.all()
    ordering = ["-created_at", "name"]
    ordering_fields = ["created_at", "name"]
    search_fields = ["name"]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return TakeawayType.objects.filter(takeaways__note__project=project)
