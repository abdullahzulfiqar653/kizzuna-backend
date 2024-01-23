import json

from django.db.models import Count
from django.db.models.query import QuerySet
from django.utils.translation import gettext
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utils.openai_functions import (
    convert_pydantic_to_openai_function,
)
from pydantic import BaseModel, Field, constr
from tiktoken import encoding_for_model

from api.ai import config
from api.models.note import Note
from api.models.tag import Tag
from api.models.takeaway import Takeaway

__all__ = ["generate_tag"]

encoder = encoding_for_model(config.model)


def generate_tags(note: Note):
    chunked_takeaway_lists = chunk_takeaway_list(note)
    chain = get_chain()

    results = []
    for takeaway_list in chunked_takeaway_lists:
        data = {"takeaways": takeaway_list}
        takeaways = json.dumps(data)
        result = chain.invoke({"takeaways": takeaways})
        results.extend(result["takeaways"])
    tags = save_tags(note, results)
    save_takeaway_tags(note, tags, results)
    update_takeaway_count(note, tags)


def get_chain():
    class TakeawaySchema(BaseModel):
        __doc__ = gettext(
            """
            The id and the corresponding generated tags.
            """
        )

        id: str = Field(
            description=gettext("ID of the takeaway. For example: '322xBv9XpAbD'")
        )
        tags: list[constr(max_length=50)] = Field(
            description=gettext("List of generated tags")
        )

    class TakeawayListSchema(BaseModel):
        __doc__ = gettext("""A list of takeaways with their relevant tags.""")

        takeaways: list[TakeawaySchema]

    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext("Generate tags for each of the given takeaways."),
            ),
            ("human", "{takeaways}"),
        ]
    )
    openai_functions = [convert_pydantic_to_openai_function(TakeawayListSchema)]
    parser = JsonOutputFunctionsParser()
    chain = prompt | llm.bind(functions=openai_functions) | parser
    return chain


def chunk_takeaway_list(note: Note):
    token_count = 0
    chunked_takeaway_lists = [[]]
    for takeaway in note.takeaways.all():
        token_count += len(encoder.encode(takeaway.title))
        if token_count < 1000:
            chunked_takeaway_lists[-1].append(
                {"id": takeaway.id, "message": takeaway.title}
            )
        else:  # token_count >= 1000
            chunked_takeaway_lists.append(
                [{"id": takeaway.id, "message": takeaway.title}]
            )
            token_count = 0
    return chunked_takeaway_lists


def save_tags(note: Note, results) -> QuerySet[Tag]:
    tags_to_add = [
        Tag(name=tag_name, project=note.project)
        for takeaway in results
        for tag_name in takeaway["tags"]
    ]
    Tag.objects.bulk_create(tags_to_add, ignore_conflicts=True)
    tag_names = [tag.name for tag in tags_to_add]
    tags = Tag.objects.filter(name__in=tag_names, project=note.project)
    return tags


def save_takeaway_tags(note: Takeaway, tags: QuerySet[Tag], results):
    get_tag = {tag.name.lower(): tag for tag in tags}
    get_takeaway = {takeaway.id: takeaway for takeaway in note.takeaways.all()}
    TakeawayTag = Takeaway.tags.through
    takeaway_tags = []
    for takeaway_data in results:
        takeaway: Takeaway = get_takeaway[takeaway_data["id"]]
        for tag_name in takeaway_data["tags"]:
            tag = get_tag[tag_name.lower()]
            takeaway_tags.append(TakeawayTag(takeaway=takeaway, tag=tag))
    TakeawayTag.objects.bulk_create(takeaway_tags, ignore_conflicts=True)


def update_takeaway_count(note: Note, tags: QuerySet[Tag]):
    tag_names = [tag.name for tag in tags]
    tags = Tag.objects.filter(name__in=tag_names, project=note.project).annotate(
        new_takeaway_count=Count("takeaways")
    )
    for tag in tags:
        tag.takeaway_count = tag.new_takeaway_count
    Tag.objects.bulk_update(tags, ["takeaway_count"])
