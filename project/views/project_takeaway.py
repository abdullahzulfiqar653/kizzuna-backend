from rest_framework import exceptions, generics

from takeaway.filters import TakeawayFilter
from takeaway.models import Takeaway
from takeaway.serializers import TakeawaySerializer


class ProjectTakeawayListView(generics.ListAPIView):
    serializer_class = TakeawaySerializer
    filterset_class = TakeawayFilter
    ordering_fields = [
        'created_at',
        'created_by__first_name',
        'created_by__last_name',
        'title',
    ]
    ordering = ['created_at']
    search_fields = [
        'title',
        'created_by__username',
        'created_by__first_name',
        'created_by__last_name',
    ]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return Takeaway.objects.filter(note__project=project)
