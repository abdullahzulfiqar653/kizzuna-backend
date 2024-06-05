from rest_framework import generics

from api.models.property import Property
from api.serializers.property import PropertySerializer


class ProjectPropertyListCreateView(generics.ListCreateAPIView):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    ordering = ["order"]

    def get_queryset(self):
        return self.request.project.properties.all()

    def perform_create(self, serializer):
        serializer.save(project=self.request.project)
