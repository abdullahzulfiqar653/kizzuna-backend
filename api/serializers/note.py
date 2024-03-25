# note/serializers.py
import logging

from django.db.models import Count
from rest_framework import exceptions, serializers

from api.models.highlight import Highlight
from api.models.keyword import Keyword
from api.models.note import Note
from api.models.organization import Organization
from api.models.question import Question
from api.serializers.organization import OrganizationSerializer
from api.serializers.question import QuestionSerializer
from api.serializers.tag import KeywordSerializer
from api.serializers.user import UserSerializer

logger = logging.getLogger(__name__)


class NoteSerializer(serializers.ModelSerializer):
    file_name = serializers.CharField(read_only=True, source="file.name")
    takeaway_count = serializers.IntegerField(read_only=True)
    author = UserSerializer(read_only=True)
    keywords = KeywordSerializer(many=True, required=False)
    questions = QuestionSerializer(many=True, required=False)
    summary = serializers.JSONField(required=False, default=[])
    organizations = OrganizationSerializer(many=True, required=False)

    class Meta:
        model = Note
        fields = [
            "id",
            "code",
            "takeaway_count",
            "author",
            "is_analyzing",
            "is_auto_tagged",
            "keywords",
            "questions",
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
            "file_type",
            "file_name",
            "url",
            "sentiment",
        ]
        read_only_fields = [
            "id",
            "code",
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
                "default": "User Interview",
            },
            "description": {
                "required": False,
                "default": "",
            },
        }

    def validate_questions(self, value):
        if len(value) > 8:
            raise exceptions.ValidationError("Please provide at most 8 questions.")
        return value

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

    def add_questions(self, note, questions):
        questions_to_create = [
            Question(title=question["title"], project=note.project)
            for question in questions
        ]
        Question.objects.bulk_create(questions_to_create, ignore_conflicts=True)
        questions_to_add = Question.objects.filter(project=note.project).filter(
            title__in=[question["title"] for question in questions]
        )
        note.questions.add(*questions_to_add)

    def create(self, validated_data):
        if validated_data["file"] is not None:
            validated_data["file_size"] = validated_data["file"].size
        organizations = validated_data.pop("organizations", [])
        keywords = validated_data.pop("keywords", [])
        questions = validated_data.pop("questions", [])
        note = Note.objects.create(**validated_data)
        self.add_organizations(note, organizations)
        self.add_keywords(note, keywords)
        self.add_questions(note, questions)
        return note


class NoteUpdateSerializer(NoteSerializer):
    """
    Do not allow users to update keywords and questions through note endpoint directly.
    They should use the dedicated endpoints to update keywords and questions instead.
    """

    keywords = None
    questions = None

    class Meta(NoteSerializer.Meta):
        fields = list(set(NoteSerializer.Meta.fields) - {"keywords", "questions"})

    def update(self, note: Note, validated_data):
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


class ProjectNoteTypeSerializer(serializers.Serializer):
    name = serializers.CharField()
    report_count = serializers.IntegerField()


class ProjectSentimentSerializer(serializers.Serializer):
    name = serializers.ChoiceField(choices=Note.Sentiment.choices)
    report_count = serializers.IntegerField()
