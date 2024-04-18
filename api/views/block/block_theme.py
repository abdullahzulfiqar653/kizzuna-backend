from rest_framework import generics

from api.models.theme import Theme
from api.serializers.theme import ThemeSerializer


class BlockThemeListCreateView(generics.ListCreateAPIView):
    queryset = Theme.objects.all()
    serializer_class = ThemeSerializer

    def get_queryset(self):
        return self.request.block.themes.all()
