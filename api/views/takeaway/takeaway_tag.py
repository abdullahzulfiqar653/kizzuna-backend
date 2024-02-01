from rest_framework import exceptions, generics, status
from rest_framework.response import Response

from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.serializers.tag import TagSerializer
from api.serializers.takeaway import TakeawaySerializer


class TakeawayTagCreateView(generics.CreateAPIView):
    serializer_class = TagSerializer

    def create(self, request, takeaway_id):
        serializer = TagSerializer(
            data={**request.data, "project": request.takeaway.note.project.id}
        )
        serializer.is_valid(raise_exception=True)
        tag = serializer.save()
        request.takeaway.tags.add(tag)
        return Response(serializer.data)


class TakeawayTagDestroyView(generics.DestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    takeaway_queryset = Takeaway.objects.all()
    takeaway_serializer_class = TakeawaySerializer

    def destroy(self, request, takeaway_id, tag_id):
        try:
            tag = self.get_queryset().get(pk=tag_id)
        except Takeaway.DoesNotExist or Tag.DoesNotExist:
            raise exceptions.NotFound(f"Tag {tag_id} not found")

        request.takeaway.tags.remove(tag)
        return Response(status=status.HTTP_204_NO_CONTENT)
