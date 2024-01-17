# note/serializers.py
import logging

from django.db.models import Count
from rest_framework import serializers

from api.models.highlight import Highlight
from api.models.keyword import Keyword
from api.models.note import Note
from api.models.organization import Organization
from api.serializers.organization import OrganizationSerializer
from api.serializers.tag import KeywordSerializer
from api.serializers.takeaway import HighlightSerializer
from api.serializers.user import UserSerializer

logger = logging.getLogger(__name__)


class SkipIdValidatorHighlightSerializer(HighlightSerializer):
    id = serializers.CharField(read_only=False)

    class Meta:
        model = Highlight
        fields = [
            "id",
            "start",
            "end",
        ]
        extra_kwargs = {
            "id": {
                "validators": [],
            },
        }


class NoteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    title = serializers.CharField(required=False, default="New Report")
    type = serializers.CharField(required=False, default="User Interview")
    description = serializers.CharField(required=False, default="")
    code = serializers.CharField(read_only=True)
    takeaway_count = serializers.IntegerField(read_only=True)
    author = UserSerializer(read_only=True)
    is_analyzing = serializers.BooleanField(read_only=True)
    is_auto_tagged = serializers.BooleanField(read_only=True)
    file_type = serializers.CharField(read_only=True)
    keywords = KeywordSerializer(many=True, required=False)
    summary = serializers.CharField(required=False, default="", allow_blank=True)
    organizations = OrganizationSerializer(many=True)

    class Meta:
        model = Note
        fields = [
            "id",
            "code",
            "takeaway_count",
            "author",
            "is_analyzing",
            "is_auto_tagged",
            "file_type",
            "keywords",
            "summary",
            "title",
            "created_at",
            "organizations",
            "content",
            "revenue",
            "description",
            "type",
            "is_published",
            "file",
            "url",
            "sentiment",
        ]

    def create(self, validated_data):
        project_id = self.context["view"].kwargs["project_id"]
        organizations = validated_data.pop("organizations", [])
        keywords = validated_data.pop("keywords", [])
        note = Note.objects.create(**validated_data)

        for organization_dict in organizations:
            organization_name = organization_dict["name"]
            organization, _ = Organization.objects.get_or_create(
                name=organization_name, project_id=project_id
            )
            note.organizations.add(organization)

        for keyword_dict in keywords:
            keyword_name = keyword_dict["name"]
            keyword, _ = Keyword.objects.get_or_create(name=keyword_name)
            note.keywords.add(keyword)

        return note

    def update(self, note: Note, validated_data):
        request = self.context["request"]
        project = note.project
        organizations = validated_data.pop("organizations", None)
        note = super().update(note, validated_data)

        note = self.extract_highlights_from_content_state(note)

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

    def extract_highlights_from_content_state(self, note):
        # Extract highlights from rich text and update
        request = self.context["request"]
        if note.content is None:
            note.highlights.delete()
        else:  # note.content is not None
            input_highlights = dict()
            new_highlight_id = None
            for block in note.content["blocks"]:
                for srange in block.get("inlineStyleRanges", []):
                    if srange["style"] != "HIGHLIGHT":
                        continue
                    highlight_id = srange.get("id")
                    if highlight_id is None:
                        if new_highlight_id is None:
                            highlight = Highlight.objects.create(
                                note=note,
                                created_by=request.user,
                            )
                            highlight_id = highlight.id
                            new_highlight_id = highlight_id
                        else:  # new_highlight_id is not None
                            # All the highlights without highlight id will consider as
                            # one single new highlight
                            highlight_id = new_highlight_id
                        # Add the highlight id for the highlights in
                        # the note.content inlineStyleRanges
                        srange["id"] = highlight_id
                    start = srange["offset"]
                    end = srange["offset"] + srange["length"]
                    highlighted_text = block["text"][start:end]
                    input_highlights.setdefault(highlight_id, "")
                    input_highlights[highlight_id] += highlighted_text

            db_highlights = {
                highlight.id: highlight
                for highlight in Highlight.objects.filter(note=note)
            }
            highlights_to_update = []
            for highlight_id, highlight_title in input_highlights.items():
                highlight = db_highlights.get(highlight_id)
                if highlight is None:
                    # The highlight id in the note.content doesn't match with
                    # any of the highlights in the db. Will skip it.
                    logger.warn(
                        f"The highlight {highlight_id} is not found and skipped."
                    )
                    continue
                highlight.title = highlight_title
                highlights_to_update.append(highlight)
            Highlight.objects.bulk_update(highlights_to_update, ["title"])
            note.highlights.exclude(id__in=input_highlights.keys()).delete()
            # We save the note again as we have added the highlight id
            # to the newly created highlight in the content state.
            note.save()
        return note


class ProjectNoteSerializer(NoteSerializer):
    content = None
    highlights = None

    class Meta(NoteSerializer.Meta):
        fields = list(set(NoteSerializer.Meta.fields) - {"content", "highlights"})


class ProjectTypeSerializer(serializers.Serializer):
    name = serializers.CharField()
    report_count = serializers.IntegerField()


class ProjectSentimentSerializer(serializers.Serializer):
    name = serializers.ChoiceField(choices=Note.Sentiment.choices)
    report_count = serializers.IntegerField()
