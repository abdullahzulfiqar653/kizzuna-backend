from rest_framework import exceptions, generics

from tag.models import Tag
from tag.serializers import TagSerializer


class ProjectTakeawayTagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    ordering = ['name']

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return Tag.objects.filter(takeaway__note__project=project)
