from rest_framework import generics

from api.models.theme import Theme
from api.serializers.theme import ThemeSerializer


class ThemeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer
