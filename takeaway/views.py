from django.shortcuts import get_object_or_404
from rest_framework import exceptions, generics, status
from rest_framework.response import Response

from tag.models import Tag
from tag.serializers import TagSerializer
from takeaway.models import Insight, Takeaway
from takeaway.serializers import InsightSerializer, TakeawaySerializer


class TakeawayRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer

    def get_queryset(self):
        return Takeaway.objects.filter(note__project__users=self.request.user)


class TakeawayTagCreateView(generics.CreateAPIView):
    serializer_class = TagSerializer

    def create(self, request, takeaway_id):
        takeaway = get_object_or_404(Takeaway, id=takeaway_id)
        project = takeaway.note.project
        if not project.users.contains(request.user):
            raise exceptions.PermissionDenied

        serializer = TagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tag = serializer.save()
        takeaway.tags.add(tag)
        return Response(serializer.data)


class TakeawayTagDestroyView(generics.DestroyAPIView):
    takeaway_queryset = Takeaway.objects.all()
    tag_queryset = Tag.objects.all()
    takeaway_serializer_class = TakeawaySerializer
    tag_serializer_class = TagSerializer

    def destroy(self, request, takeaway_id, tag_id):
        try:
            takeaway = self.takeaway_queryset.get(pk=takeaway_id)
            tag = self.tag_queryset.get(pk=tag_id)
        except Takeaway.DoesNotExist or Tag.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if not takeaway.note.project.users.contains(request.user):
            raise exceptions.PermissionDenied

        # Check if the tag is related to the takeaway
        if takeaway.tags.filter(pk=tag_id).exists():
            # Remove the association between takeaway and tag
            takeaway.tags.remove(tag)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {"detail": "Tag is not associated with the specified takeaway."},
                status=status.HTTP_400_BAD_REQUEST
            )


class InsightRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Insight.objects.all()
    serializer_class = InsightSerializer

    def get_queryset(self):
        return Insight.objects.filter(project__users=self.request.user)


class InsightTakeawayCreateView(generics.CreateAPIView):
    queryset = Insight.objects.all()

    def create(self, request, insight_id, takeaway_id):
        insight = Insight.objects.filter(id=insight_id, project__users=request.user).first()
        if insight is None:
            raise exceptions.NotFound('Insight not found.')

        takeaway = Takeaway.objects.filter(id=takeaway_id, note__project=insight.project).first()
        if takeaway is None:
            raise exceptions.NotFound('Takeaway not found.')

        insight.takeaways.add(takeaway)
        return Response({'id': takeaway_id}, status=status.HTTP_201_CREATED)
