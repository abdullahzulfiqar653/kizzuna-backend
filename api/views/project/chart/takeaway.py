from drf_spectacular.utils import extend_schema
from rest_framework import generics, response

from api.models.takeaway import Takeaway
from api.permissions import IsWorkspaceMemberFullAccess
from api.serializers.chart.takeaway import ChartTakeawaySerializer


@extend_schema(responses={201: None})
class ChartTakeawayCreateView(generics.CreateAPIView):
    serializer_class = ChartTakeawaySerializer
    queryset = Takeaway.objects.all()
    permission_classes = [IsWorkspaceMemberFullAccess]

    def get_queryset(self):
        return Takeaway.objects.filter(
            note__project=self.request.project, note__is_shared=True
        )

    def create(self, request, project_id):
        queryset = self.get_queryset()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = serializer.query(queryset)
        return response.Response(queryset)
