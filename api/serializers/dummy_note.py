import ast
import json

import shortuuid
from django.conf import settings
from rest_framework import exceptions, serializers

from api.models.feature import Feature
from api.models.highlight import Highlight
from api.models.note import Note
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.utils.lexical import LexicalProcessor


class DummyNoteCreateSerializer(serializers.Serializer):
    def create(self, validated_data):
        request = self.context.get("request")
        workspace = request.project.workspace
        notes_limit = workspace.get_feature_value(
            Feature.Code.NUMBER_OF_KNOWLEDGE_SOURCES
        )
        if workspace.notes.count() >= notes_limit:
            raise exceptions.PermissionDenied(
                f"You have reached the limit of {notes_limit} Knowledge sources."
            )
        try:
            path = f"{settings.BASE_DIR}/api/fixtures/dummy_notes"

            with open(f"{path}/dummy_notes.json", "r") as file:
                dummy_notes = json.load(file)

            with open(f"{path}/dummy_takeaways.json", "r") as file:
                dummy_takeaways = json.load(file)

            with open(f"{path}/dummy_highlights.json", "r") as file:
                dummy_highlights = json.load(file)

            with open(f"{path}/dummy_takeaway_types.json", "r") as file:
                dummy_takeaway_types = json.load(file)

            with open(f"{path}/dummy_tags.json", "r") as file:
                dummy_tags = json.load(file)

        except:
            serializers.ValidationError(
                "Something bad happend while adding knowledge sources."
            )

        note_type = request.project.note_types.get(name="User Interview")

        # Build takeaway type mapping
        takeaway_type_by_name = {
            takeaway_type.name: takeaway_type
            for takeaway_type in TakeawayType.objects.filter(project=request.project)
        }
        takeaway_type_mapping = {
            dummy_takeaway_type["pk"]: takeaway_type_by_name.get(
                dummy_takeaway_type["fields"]["name"]
            )
            for dummy_takeaway_type in dummy_takeaway_types
        }

        # Build quote mapping
        quote_mapping = {
            dummy_highlight["pk"]: dummy_highlight["fields"]["quote"]
            for dummy_highlight in dummy_highlights
        }

        # Build tag mapping
        Tag.objects.bulk_create(
            [
                Tag(name=dummy_tag["fields"]["name"], project=request.project)
                for dummy_tag in dummy_tags
            ],
            ignore_conflicts=True,
        )
        tag_by_name = {tag.name: tag for tag in request.project.tags.all()}
        tag_mapping = {
            dummy_tag["pk"]: tag_by_name[dummy_tag["fields"]["name"]]
            for dummy_tag in dummy_tags
        }

        # Create notes
        notes_to_create = []
        id_mapping = {}
        note_mapping = {}
        bot = User.objects.get(username="bot@raijin.ai")
        for dummy_note in dummy_notes:
            fields = dummy_note["fields"]
            lexical = LexicalProcessor(fields["content"]["root"])
            for mark in lexical.find_all("mark", recursive=True):
                mark.dict["ids"] = [
                    id_mapping.setdefault(
                        old_id, shortuuid.ShortUUID().random(length=12)
                    )
                    for old_id in mark.dict["ids"]
                ]

            note = Note(
                title=fields["title"],
                author=request.user,
                project=request.project,
                workspace=workspace,
                type=note_type,
                description=fields["description"],
                content=fields["content"],
                summary=fields["summary"],
                sentiment=Note.Sentiment.POSITIVE,
            )
            notes_to_create.append(note)
            note_mapping[dummy_note["pk"]] = note
        Note.objects.bulk_create(notes_to_create)

        # Create takeaways
        takeaways_to_create = []
        highlights_to_create = []
        takeaway_tags_to_create = []
        for dummy_takeaway in dummy_takeaways:
            takeaway = Takeaway(
                id=id_mapping[dummy_takeaway["pk"]],
                title=dummy_takeaway["fields"]["title"],
                type=takeaway_type_mapping[dummy_takeaway["fields"]["type"]],
                created_by=bot,
                note=note_mapping[dummy_takeaway["fields"]["note"]],
                vector=ast.literal_eval(dummy_takeaway["fields"]["vector"]),
            )
            takeaways_to_create.append(takeaway)

            highlight = Highlight(
                takeaway_ptr_id=id_mapping[dummy_takeaway["pk"]],
                quote=quote_mapping[dummy_takeaway["pk"]],
            )
            highlights_to_create.append(highlight)

            takeaway_tags_to_create.extend(
                [
                    Highlight.tags.through(
                        takeaway_id=id_mapping[dummy_takeaway["pk"]],
                        tag=tag_mapping[dummy_tag_id],
                    )
                    for dummy_tag_id in dummy_takeaway["fields"]["tags"]
                ]
            )
        Takeaway.objects.bulk_create(takeaways_to_create)
        Highlight.bulk_create(highlights_to_create)
        Highlight.tags.through.objects.bulk_create(takeaway_tags_to_create)
        return {}
