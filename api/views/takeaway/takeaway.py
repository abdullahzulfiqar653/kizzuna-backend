from rest_framework import generics, status
from rest_framework.response import Response

from api.models.note import Note
from api.models.takeaway import Takeaway
from api.serializers.takeaway import TakeawaySerializer
from api.utils.lexical import LexicalProcessor


class TakeawayRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer

    def destroy(self, request, *args, **kwargs):
        takeaway: Takeaway = self.get_object()
        note: Note = takeaway.note

        # Clean up highlight
        if hasattr(takeaway, "highlight"):
            # This takeaway is a highlight.
            # Need to remove the highlight from note.content
            root = LexicalProcessor(note.content["root"])
            node_to_handle = lambda node: (
                node.dict["type"] == "mark"
                and takeaway.highlight.id in node.dict["ids"]
            )
            for node in root.find_all(node_to_handle, recursive=True):
                node.dict["ids"].remove(takeaway.highlight.id)
                if len(node.dict["ids"]) == 0:
                    # Remove the "mark" node and move its children up one level
                    i = node.parent.dict["children"].index(node.dict)
                    node.parent.dict["children"][i : i + 1] = node.dict["children"]
        note.save()

        self.perform_destroy(takeaway)
        return Response(status=status.HTTP_204_NO_CONTENT)
