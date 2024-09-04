# note/serializers.py
import logging
import tempfile

import requests
from django.core.files.base import ContentFile
from django.db.models import Count
from rest_framework import exceptions, serializers

from api.ai.embedder import embedder
from api.mixpanel import mixpanel
from api.models.highlight import Highlight
from api.models.integrations.google.credential import GoogleCredential
from api.models.keyword import Keyword
from api.models.note import Note
from api.models.note_type import NoteType
from api.models.organization import Organization
from api.serializers.note_type import NoteTypeSerializer
from api.serializers.organization import OrganizationSerializer
from api.serializers.tag import KeywordSerializer
from api.serializers.user import UserSerializer
from api.utils import media
from api.utils.lexical import LexicalProcessor

logger = logging.getLogger(__name__)


class NoteSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(read_only=True, source="file.name")
    takeaway_count = serializers.IntegerField(read_only=True)
    author = UserSerializer(read_only=True)
    keywords = KeywordSerializer(many=True, required=False)
    summary = serializers.JSONField(required=False, default=[])
    organizations = OrganizationSerializer(many=True, required=False)
    google_drive_file_id = serializers.CharField(write_only=True, required=False)
    is_analyzing = serializers.BooleanField(read_only=True)
    type = NoteTypeSerializer(read_only=True)
    type_id = serializers.PrimaryKeyRelatedField(
        source="type",
        queryset=NoteType.objects.none(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Note
        fields = [
            "id",
            "takeaway_count",
            "author",
            "is_analyzing",
            "is_auto_tagged",
            "keywords",
            "summary",
            "title",
            "created_at",
            "organizations",
            "is_approved",
            "content",
            "transcript",
            "revenue",
            "description",
            "type",
            "type_id",
            "file",
            "file_type",
            "media_type",
            "file_name",
            "url",
            "sentiment",
            "slack_channel_id",
            "slack_team_id",
            "google_drive_file_id",
            "google_drive_file_timestamp",
        ]
        read_only_fields = [
            "id",
            "author",
            "is_analyzing",
            "is_auto_tagged",
            "file_type",
        ]
        extra_kwargs = {
            "title": {
                "required": False,
                "default": "New Source",
            },
            "type": {
                "required": False,
                "default": "Unassigned",
            },
            "description": {
                "required": False,
                "default": "",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if hasattr(request, "project"):
            self.fields["type_id"].queryset = request.project.note_types.all()
        elif hasattr(request, "note"):
            self.fields["type_id"].queryset = request.note.project.note_types.all()

    def validate_content(self, content):
        text = LexicalProcessor(content["root"]).to_markdown()
        if len(text) > 250_000:
            raise exceptions.ValidationError("Content exceed length limit.")
        return content

    def validate(self, data):
        slack_team_id = data.get("slack_team_id")
        slack_channel_id = data.get("slack_channel_id")

        if (slack_team_id is None and slack_channel_id is not None) or (
            slack_team_id is not None and slack_channel_id is None
        ):
            raise serializers.ValidationError(
                "slack_team_id and slack_channel_id must either both be non-null or both be null."
            )

        return data

    def add_organizations(self, note, organizations):
        organizations_to_create = [
            Organization(name=organization["name"], project=note.project)
            for organization in organizations
        ]
        Organization.objects.bulk_create(organizations_to_create, ignore_conflicts=True)
        organizations_to_add = Organization.objects.filter(project=note.project).filter(
            name__in=[organization["name"] for organization in organizations]
        )
        note.organizations.add(*organizations_to_add)

    def add_keywords(self, note, keywords):
        keywords_to_create = [Keyword(name=keyword["name"]) for keyword in keywords]
        Keyword.objects.bulk_create(keywords_to_create, ignore_conflicts=True)
        keywords_to_add = Keyword.objects.filter(
            name__in=[keyword["name"] for keyword in keywords]
        )
        note.keywords.add(*keywords_to_add)

    def create(self, validated_data):
        google_drive_file_id = validated_data.pop("google_drive_file_id", None)

        if google_drive_file_id:
            user = self.context["request"].user
            try:
                gdrive_user = GoogleCredential.objects.get(user=user)
            except GoogleCredential.DoesNotExist:
                raise serializers.ValidationError("Google Drive account not connected")

            headers = {"Authorization": f"Bearer {gdrive_user.token}"}

            file_metadata_response = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{google_drive_file_id}?fields=name,mimeType,size,createdTime",
                headers=headers,
            )
            file_metadata_response.raise_for_status()
            file_metadata = file_metadata_response.json()

            file_content_response = requests.get(
                f"https://www.googleapis.com/drive/v3/files/{google_drive_file_id}?alt=media",
                headers=headers,
            )
            file_content_response.raise_for_status()
            file_content = file_content_response.content

            validated_data["title"] = file_metadata.get("name")
            validated_data["file"] = ContentFile(
                file_content, name=file_metadata.get("name")
            )
            validated_data["file_type"] = file_metadata.get("mimeType")
            validated_data["file_size"] = file_metadata.get("size")
            validated_data["google_drive_file_timestamp"] = file_metadata.get(
                "createdTime"
            )
        organizations = validated_data.pop("organizations", [])
        keywords = validated_data.pop("keywords", [])
        file = validated_data.get("file")

        # Convert mp4 file with movflags faststart for streaming
        if file and file.name and file.name.split(".")[-1].lower() == "mp4":
            with tempfile.NamedTemporaryFile(suffix=".mp4") as output:
                validated_data["file"] = media.process_mp4_for_streaming(file, output)
                note = Note.objects.create(**validated_data)
        else:
            note = Note.objects.create(**validated_data)
        self.add_organizations(note, organizations)
        self.add_keywords(note, keywords)
        mixpanel.track(
            note.author.id,
            "BE: Knowledge Source Created",
            {"source_id": note.id, "project_id": note.project.id},
        )
        return note


class NoteUpdateSerializer(NoteSerializer):
    """
    Do not allow users to update keywords through note endpoint directly.
    They should use the dedicated endpoints to update keywords instead.
    """

    keywords = None

    class Meta(NoteSerializer.Meta):
        fields = list(set(NoteSerializer.Meta.fields) - {"keywords"})

    def update(self, note: Note, validated_data):
        if note.is_analyzing:
            raise exceptions.ValidationError("Cannot update an analyzing note.")
        project = note.project
        organizations = validated_data.pop("organizations", None)
        note = super().update(note, validated_data)

        if note.media_type is Note.MediaType.TEXT:
            note = self.extract_highlights_from_content_state(note)
        else:
            self.update_highlights(note)

        if organizations is not None:
            organizations_to_add = []
            for organization_dict in organizations:
                organization_name = organization_dict["name"]
                organization, _ = Organization.objects.get_or_create(
                    name=organization_name, project=project
                )
                organizations_to_add.append(organization)
            note.organizations.set(organizations_to_add)
            # Clean up
            (
                Organization.objects.filter(project=project)
                .annotate(note_count=Count("notes"))
                .filter(note_count=0)
                .delete()
            )

        return note

    def extract_input_highlights(self, root: LexicalProcessor, new_highlight_id: str):
        input_highlights = {}
        for node in root.find_all("mark", recursive=True):
            if None in node.dict["ids"]:
                # Replace None with the new highlight id
                # and keep the other non-None ids.
                node.dict["ids"] = [
                    id if id is not None else new_highlight_id
                    for id in node.dict["ids"]
                ]
            for id in node.dict["ids"]:
                input_highlights.setdefault(id, "")
                input_highlights[id] += node.to_text()
        return input_highlights

    def extract_highlights_from_content_state(self, note):
        # Extract highlights from rich text and update
        request = self.context["request"]
        new_highlight_id = Highlight.id.field._generate_uuid()
        root = LexicalProcessor(note.content["root"])
        input_highlights = self.extract_input_highlights(root, new_highlight_id)
        if new_highlight_id in input_highlights:
            new_highlight_text = input_highlights.get(new_highlight_id)
            Highlight.objects.create(
                id=new_highlight_id,
                title=new_highlight_text,
                quote=new_highlight_text,
                vector=embedder.embed_documents([new_highlight_text])[0],
                note=note,
                created_by=request.user,
            )

        db_highlights = {
            highlight.id: highlight for highlight in Highlight.objects.filter(note=note)
        }
        highlights_to_update = []
        for highlight_id, highlight_title in input_highlights.items():
            highlight = db_highlights.get(highlight_id)
            if highlight is None:
                # The highlight id in the note.content doesn't match with
                # any of the highlights in the db. Will skip it.
                print(highlight_id)
                logger.warn(f"The highlight {highlight_id} is not found and skipped.")
                continue
            if highlight.quote == highlight_title:
                # No need to update the highlight if the title is the same.
                continue
            highlight.quote = highlight_title
            highlight.vector = embedder.embed_documents([highlight_title])[0]
            highlights_to_update.append(highlight)
        Highlight.objects.bulk_update(highlights_to_update, ["quote", "vector"])
        note.highlights.exclude(id__in=input_highlights.keys()).delete()
        # We save the note again as we have added the highlight id
        # to the newly created highlight in the content state.
        note.save()
        return note

    def update_highlights(self, note):
        highlights_to_update = {}

        for utterance in note.transcript.get("utterances", []):
            for word in utterance.get("words", []):
                for highlight_id in word.get("highlight_ids", []):
                    highlights_to_update.setdefault(highlight_id, []).append(
                        word["text"]
                    )

        highlight_ids = list(highlights_to_update.keys())
        highlights = {
            highlight.takeaway_ptr_id: highlight
            for highlight in Highlight.objects.filter(takeaway_ptr_id__in=highlight_ids)
        }

        for highlight_id, words in highlights_to_update.items():
            highlight = highlights[highlight_id]
            highlight.quote = " ".join(words)
        Highlight.objects.bulk_update(highlights.values(), ["quote", "title", "vector"])


class ProjectNoteSerializer(NoteSerializer):
    content = None
    highlights = None

    class Meta(NoteSerializer.Meta):
        fields = list(set(NoteSerializer.Meta.fields) - {"content", "highlights"})


class ProjectSentimentSerializer(serializers.Serializer):
    name = serializers.ChoiceField(choices=Note.Sentiment.choices)
    report_count = serializers.IntegerField()
