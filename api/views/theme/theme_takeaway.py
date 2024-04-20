from rest_framework import generics, status
from rest_framework.response import Response

from api.models.takeaway import Takeaway
from api.models.theme import Theme
from api.serializers.takeaway import TakeawaySerializer, ThemeTakeawaysSerializer


class ThemeTakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()

    def get_serializer_class(self):
        match self.request.method:
            case "GET":
                return TakeawaySerializer
            case "POST":
                return ThemeTakeawaysSerializer

    def get_queryset(self):
        return TakeawaySerializer.optimize_query(
            self.request.theme.takeaways.all(), self.request.user
        )

    def get_valid_takeaways(self, theme: Theme):
        # Can add or remove any takeaways in the project to the theme
        return Takeaway.objects.filter(note__project=theme.block.asset.project)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        valid_takeaways = self.get_valid_takeaways(self.request.theme)
        context["theme"] = self.request.theme
        context["valid_takeaway_ids"] = valid_takeaways.values_list("id", flat=True)
        return context


class ThemeTakeawayDeleteView(generics.GenericAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = ThemeTakeawaysSerializer

    def get_valid_takeaways(self, theme: Theme):
        # Can add or remove any takeaways in the project to the theme
        return Takeaway.objects.filter(note__project=theme.block.asset.project)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        valid_takeaways = self.get_valid_takeaways(self.request.theme)
        context["theme"] = self.request.theme
        context["valid_takeaway_ids"] = valid_takeaways.values_list("id", flat=True)
        return context

    def post(self, request, theme_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.delete()
        return Response(serializer.data, status=status.HTTP_200_OK)
