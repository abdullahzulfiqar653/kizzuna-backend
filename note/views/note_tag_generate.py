import json
from decimal import Decimal
from pprint import pprint

from django.db.models import Count
from drf_spectacular.utils import extend_schema
from langchain.callbacks import get_openai_callback
from langchain.chains.openai_functions import create_structured_output_chain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, constr
from rest_framework import exceptions, generics, status
from rest_framework.response import Response
from tiktoken import encoding_for_model
from unidecode import unidecode

from note.models import Note
from tag.models import Tag
from takeaway.models import Takeaway

encoder = encoding_for_model("gpt-3.5-turbo")


class TakeawaySchema(BaseModel):
    message: str = Field(description="message of the takeaway.")
    tags: list[constr(max_length=50)] = Field(
        description="Tags to be added to the takeaway."
    )


class TakeawayListSchema(BaseModel):
    takeaways: list[TakeawaySchema]


llm = ChatOpenAI()
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given the following takeaway messages, add 3 - 5 tags to each takeaway message.",
        ),
        (
            "human",
            "{takeaways}",
        ),
    ]
)
chain = create_structured_output_chain(
    TakeawayListSchema.schema(), llm, prompt, verbose=True
)


@extend_schema(request=None, responses={200: None})
class NoteTagGenerateView(generics.CreateAPIView):
    def create(self, request, report_id):
        note = Note.objects.filter(id=report_id, project__users=request.user).first()
        if note is None:
            raise exceptions.NotFound("Report not found.")

        # Chunk takeaway list
        token_count = 0
        chunked_takeaway_lists = [[]]
        for takeaway in note.takeaways.all():
            token_count += len(encoder.encode(takeaway.title))
            if token_count < 1000:
                chunked_takeaway_lists[-1].append({"message": takeaway.title})
            else:  # token_count >= 1000
                chunked_takeaway_lists.append([{"message": takeaway.title}])
                token_count = 0

        # Call OpenAI
        try:
            with get_openai_callback() as callback:
                results = []
                for takeaway_list in chunked_takeaway_lists:
                    data = {"takeaways": takeaway_list}
                    takeaways = json.dumps(data)
                    result = chain.invoke({"takeaways": takeaways})
                    pprint(result["function"])
                    results.extend(result["function"]["takeaways"])
                note.analyzing_tokens += callback.total_tokens
                note.analyzing_cost += Decimal(callback.total_cost)
            note.save()
        except:
            import traceback

            traceback.print_exc()
            return Response(
                {"details": "Failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Save tags
        tags_to_add = [
            Tag(name=tag_name, project=note.project)
            for takeaway in results
            for tag_name in takeaway["tags"]
        ]
        Tag.objects.bulk_create(tags_to_add, ignore_conflicts=True)
        tag_names = [tag.name for tag in tags_to_add]
        tags = Tag.objects.filter(name__in=tag_names, project=note.project)

        # Save takeaway tags
        get_tag = {tag.name.lower(): tag for tag in tags}
        get_takeaway = {
            unidecode(takeaway.title): takeaway for takeaway in note.takeaways.all()
        }
        TakeawayTag = Takeaway.tags.through
        takeaway_tags = []
        for takeaway_data in results:
            takeaway: Takeaway = get_takeaway[unidecode(takeaway_data["message"])]
            for tag_name in takeaway_data["tags"]:
                tag = get_tag[tag_name.lower()]
                takeaway_tags.append(TakeawayTag(takeaway=takeaway, tag=tag))
        TakeawayTag.objects.bulk_create(takeaway_tags, ignore_conflicts=True)

        # Update takeaway_count
        tags = Tag.objects.filter(name__in=tag_names, project=note.project).annotate(
            new_takeaway_count=Count("takeaways")
        )
        for tag in tags:
            tag.takeaway_count = tag.new_takeaway_count
        Tag.objects.bulk_update(tags, ["takeaway_count"])

        return Response({"details": "Successful"})
