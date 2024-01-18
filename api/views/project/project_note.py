import json

from django.core.files.uploadedfile import UploadedFile
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce, Round
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from rest_framework import exceptions, generics, serializers

from api.filters.note import NoteFilter
from api.models.note import Note
from api.models.project import Project
from api.models.workspace import Workspace
from api.serializers.note import ProjectNoteSerializer
from api.tasks import analyze_note


class ProjectNoteListCreateView(generics.ListCreateAPIView):
    queryset = Note.objects.all()
    serializer_class = ProjectNoteSerializer
    filterset_class = NoteFilter
    ordering_fields = [
        "created_at",
        "takeaway_count",
        "author__first_name",
        "author__last_name",
        "organizations__name",
        "title",
    ]
    search_fields = [
        "title",
        "author__username",
        "author__first_name",
        "author__last_name",
        "organizations__name",
    ]
    ordering = ["-created_at"]

    def get_queryset(self):
        project_id = self.kwargs["project_id"]
        project = get_object_or_404(Project, id=project_id)
        if not project.users.contains(self.request.user):
            raise exceptions.PermissionDenied
        return project.notes.annotate(
            takeaway_count=Count("takeaways"),
        )

    def get_project(self):
        project_id = self.kwargs.get("project_id")
        project = get_object_or_404(Project, id=project_id)
        if not project.users.contains(self.request.user):
            raise exceptions.PermissionDenied
        return project

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

    def check_eligibility(self, project: Project):
        workspace = (
            Workspace.objects.filter(id=project.workspace.id)
            .annotate(
                usage_minutes=Coalesce(
                    Round(Sum("projects__notes__file_duration_seconds") / 60),
                    0,
                )
            )
            .annotate(
                usage_tokens=Coalesce(Sum("projects__notes__analyzing_tokens"), 0)
            )
            .first()
        )
        if (workspace.usage_minutes > 60) or (workspace.usage_tokens > 50_000):
            raise exceptions.PermissionDenied("Quota limit is hit.")

    def perform_create(self, serializer):
        project = self.get_project()
        # self.check_eligibility(project)
        note = serializer.save(author=self.request.user, project=project)
        if note.file or note.url:
            analyze_note.delay(note.id)
