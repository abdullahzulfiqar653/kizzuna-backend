import json

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.http.request import QueryDict
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import exceptions, generics, response, serializers
from rest_framework.permissions import AllowAny

from api.ai.analyzer.note_analyzer import ExistingNoteAnalyzer, NewNoteAnalyzer
from api.models.project import Project
from api.serializers.note import NoteSerializer
from api.serializers.takeaway import TakeawaySerializer


@extend_schema(request=NoteSerializer, responses={200: TakeawaySerializer(many=True)})
class DemoGenerateTakeawaysCreateView(generics.CreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [AllowAny]

    def to_dict(self, form_data):
        data_file = form_data.get("data")
        if not isinstance(data_file, UploadedFile):
            raise serializers.ValidationError("`data` field must be a blob.")
        data = json.load(data_file)
        data["file"] = form_data.get("file")
        return data

    def get_serializer(self, *args, **kwargs):
        # Convert data to json if the request is multipart form
        data = kwargs.get("data")

        if data is None:
            # If it is not POST request, data is None
            return super().get_serializer(*args, **kwargs)

        if isinstance(data, QueryDict):
            kwargs["data"] = self.to_dict(data)
            data = kwargs["data"]

        # In multipart form, null will be treated as string instead of converting to None
        # We need to manually handle the null
        if "revenue" not in data or data["revenue"] == "null":
            data["revenue"] = None

        if "file" not in data or data["file"] == "null":
            data["file"] = None

        if "url" in data and "://" not in data["url"]:
            # Django URLValidator returns invalid if no schema
            # so we manually add in the schema if not provided
            data["url"] = "http://" + data["url"]

        return super().get_serializer(*args, **kwargs)

    def check_eligibility(self, project_id, user_id):
        project = Project.objects.get(id=project_id)
        # Count notes in the project created at last 24 hours
        note_count = project.notes.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=1)
        ).count()
        if note_count >= 20:
            raise exceptions.PermissionDenied("Demo project has reached the limit.")

    def create(self, request):
        """
        To use this endpoint, create a demo project and demo user
        and set them to the env vars.
        """
        demo_project_id = settings.DEMO_PROJECT_ID
        demo_user_id = settings.DEMO_USER_ID
        if not demo_project_id or not demo_user_id:
            raise exceptions.PermissionDenied("Demo project is not set up.")

        self.check_eligibility(demo_project_id, demo_user_id)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = Project.objects.get(id=demo_project_id)
        user = project.users.get(id=demo_user_id)
        note = serializer.save(author=user, project=project)
        if note.file or note.url:
            analyzer = NewNoteAnalyzer()
            analyzer.analyze(note, user)
        elif note.content:
            analyzer = ExistingNoteAnalyzer()
            analyzer.analyze(note, user)
        takeaway_serializer = TakeawaySerializer(note.takeaways.all(), many=True)
        return response.Response(takeaway_serializer.data)
