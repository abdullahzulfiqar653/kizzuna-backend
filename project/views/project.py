from django.db.models import Prefetch, Sum
from django.db.models.functions import Round
from rest_framework import generics

from project.models import Project
from project.serializers import ProjectUsageSerializer
from workspace.models import Workspace


class ProjectRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectUsageSerializer

    def get_queryset(self):
        return self.request.user.projects.prefetch_related(
            Prefetch(
                "workspace",
                queryset=(
                    Workspace.objects.annotate(
                        usage_minutes=(
                            Round(Sum("projects__notes__file_duration_seconds") / 60.0)
                        ),
                        usage_tokens=Sum("projects__notes__analyzing_tokens"),
                    )
                ),
            )
        )
