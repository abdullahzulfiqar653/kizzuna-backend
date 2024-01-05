from rest_framework import generics, status
from rest_framework.response import Response

from note.models.note import Note
from takeaway.models import Takeaway
from takeaway.serializers import TakeawaySerializer


class TakeawayRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer

    def get_queryset(self):
        return Takeaway.objects.filter(note__project__users=self.request.user)

    def destroy(self, request, *args, **kwargs):
        takeaway: Takeaway = self.get_object()
        note: Note = takeaway.note

        if hasattr(takeaway, "highlight"):
            # This takeaway is a highlight.
            # Need to remove the highlight from note.content
            for block in note.content["blocks"]:
                block["inlineStyleRanges"] = [
                    srange
                    for srange in block["inlineStyleRanges"]
                    if not (
                        srange["style"] == "HIGHLIGHT" and srange["id"] == takeaway.id
                    )
                ]
        note.save()

        self.perform_destroy(takeaway)
        return Response(status=status.HTTP_204_NO_CONTENT)
