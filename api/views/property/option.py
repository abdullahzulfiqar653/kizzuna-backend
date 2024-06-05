from rest_framework import generics

from api.models.option import Option
from api.serializers.option import OptionSerializer


class PropertyOptionListCreateView(generics.ListCreateAPIView):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer
    ordering = ["order"]

    def get_queryset(self):
        return self.request.property.options.all()

    def perform_create(self, serializer):
        serializer.save(property=self.request.property)
