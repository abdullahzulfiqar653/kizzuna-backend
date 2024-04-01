from drf_spectacular.utils import extend_schema
from rest_framework import generics, response

from api.models.note import Note
from api.serializers.chart.note import ChartNoteSerializer


@extend_schema(responses={201: None})
class ChartNoteCreateView(generics.CreateAPIView):
    serializer_class = ChartNoteSerializer
    queryset = Note.objects.all()

    def get_queryset(self):
        return self.request.project.notes.all()

    def create(self, request, project_id):
        queryset = self.get_queryset()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        queryset = serializer.query(queryset)
        return response.Response(queryset)
