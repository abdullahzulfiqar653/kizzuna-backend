from rest_framework import exceptions, generics, status
from rest_framework.response import Response

from api.models.keyword import Keyword
from api.serializers.tag import KeywordSerializer


class NoteKeywordListCreateView(generics.ListCreateAPIView):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    ordering = ["title"]

    def get_queryset(self):
        return self.request.note.keywords.all()

    def perform_create(self, serializer):
        keyword = serializer.save()
        self.request.note.keywords.add(keyword)


class NoteKeywordDestroyView(generics.DestroyAPIView):
    serializer_class = KeywordSerializer

    def destroy(self, request, report_id, keyword_id):
        try:
            keyword = Keyword.objects.get(pk=keyword_id)
        except Keyword.DoesNotExist:
            raise exceptions.NotFound(f"Keyword {keyword_id} not found.")

        request.note.keywords.remove(keyword)
        return Response(status=status.HTTP_204_NO_CONTENT)
