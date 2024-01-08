from rest_framework import exceptions, generics

from api.models.tag import Tag
from api.serializers.tag import TagSerializer


class ProjectTagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    ordering = ["-takeaway_count", "name"]
    ordering_fields = ["created_at", "takeway_count", "name"]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return Tag.objects.filter(takeaways__note__project=project)
