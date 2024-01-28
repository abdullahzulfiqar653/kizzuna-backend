from rest_framework import generics

from api.models.organization import Organization
from api.serializers.organization import OrganizationSerializer


class ProjectOrganizationListView(generics.ListAPIView):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()
    ordering = ["name"]
    search_fields = ["name"]

    def get_queryset(self):
        return Organization.objects.filter(project=self.request.project)
