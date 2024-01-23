from decimal import Decimal

from drf_spectacular.utils import extend_schema
from langchain.callbacks import get_openai_callback
from rest_framework import exceptions, generics, status
from rest_framework.response import Response

from api.ai.generators.tag_generator import generate_tags
from api.models.note import Note


@extend_schema(request=None, responses={200: None})
class NoteTagGenerateView(generics.CreateAPIView):
    def create(self, request, report_id):
        note = Note.objects.filter(id=report_id, project__users=request.user).first()
        if note is None:
            raise exceptions.NotFound("Report not found.")

        # Call OpenAI
        try:
            with get_openai_callback() as callback:
                generate_tags(note)
                note.analyzing_tokens += callback.total_tokens
                note.analyzing_cost += Decimal(callback.total_cost)
            note.save()
        except:
            import traceback

            traceback.print_exc()
            return Response(
                {"details": "Failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({"details": "Successful"})
