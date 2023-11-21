from django.shortcuts import get_object_or_404
from rest_framework import exceptions, generics, status
from rest_framework.response import Response

from tag.models import Tag
from tag.serializers import TagSerializer
from takeaway.models import Insight, Takeaway
from takeaway.serializers import (InsightSerializer,
                                  InsightTakeawaysSerializer,
                                  TakeawaySerializer)


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


class InsightTakeawayCreateDeleteView(generics.GenericAPIView):
    queryset = Insight.objects.all()
    serializer_class = InsightTakeawaysSerializer

    def get_insight(self, insight_id):
        insight = Insight.objects.filter(id=insight_id, project__users=self.request.user).first()
        if insight is None:
            raise exceptions.NotFound('Insight not found.')
        return insight

    def get_valid_takeaway_ids(self, insight):
        valid_takeaways = Takeaway.objects.filter(note__project_id=insight.project_id)
        valid_takeaway_ids = [takeaway.id for takeaway in valid_takeaways]
        return valid_takeaway_ids

    def get_serializer_context(self):
        context = super().get_serializer_context()
        insight = self.get_insight(self.kwargs['insight_id'])
        valid_takeaway_ids = self.get_valid_takeaway_ids(insight)
        context["insight"] = insight
        context['valid_takeaway_ids'] = valid_takeaway_ids
        return context

    def post(self, request, insight_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, insight_id):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        takeaway_ids = [takeaway['id'] for takeaway in serializer.data['takeaways']]
        Takeaway.objects.filter(id__in=takeaway_ids).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
