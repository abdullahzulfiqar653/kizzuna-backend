from django.utils.translation import gettext
from langchain.chains.openai_functions import create_structured_output_chain
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from langchain_community.chat_models import ChatOpenAI
from pydantic.v1 import BaseModel, Field

from api.ai import config
from api.ai.generators.utils import token_tracker
from api.models.note import Note
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User


def get_chain():
    class TakeawaySchema(BaseModel):
        topic: str = Field(
            description=gettext("Topic of the takeaway, for grouping the takeaways.")
        )
        title: str = Field(
            description=gettext(
                "What the takeaway is about. "
                "This should be an important message, issue, learning point "
                "or pain point of the text."
            )
        )
        significance: str = Field(
            description=gettext("The reason why the takeaway is important.")
        )
        type: str = Field(
            description=gettext(
                "The takeaway type. For example: 'Pain Point', 'Feature', 'Idea'."
            )
        )

    class TakeawaysSchema(BaseModel):
        takeaways: list[TakeawaySchema] = Field(
            description=gettext(
                "A list of ten to twenty important takeaways of the text."
            ),
        )

    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext(
                    "You are an experienced product analyst. "
                    "You are experienced in identifying pain points "
                    "and takeaways from user interviews."
                ),
            ),
            (
                "human",
                gettext(
                    "Identify Important Takeaways/Issues/Learning Points "
                    "in the below given text and reasons why they are important."
                )
                + "\n\n{text}",
            ),
        ]
    )
    takeaways_chain = create_structured_output_chain(TakeawaysSchema, llm, prompt)
    return takeaways_chain


def generate_takeaways_default_question(note: Note, created_by: User):
    takeaways_chain = get_chain()

    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    bot = User.objects.get(username="bot@raijin.ai")
    doc = Document(page_content=note.get_content_text())
    docs = text_splitter.split_documents([doc])
    with token_tracker(note.project, note, "generate-takeaways", created_by):
        outputs = [takeaways_chain.invoke(doc.page_content) for doc in docs]

    # Post processing the LLM response
    generated_takeaways = [
        {
            "title": f'{takeaway["topic"]} - {takeaway["title"]}: {takeaway["significance"]}',
            "type": takeaway["type"],
        }
        for output in outputs
        for takeaway in output["function"].dict()["takeaways"]
    ]

    # Create new takeaway types
    existing_takeaway_types = set(
        TakeawayType.objects.filter(project=note.project).values_list("name", flat=True)
    )
    generated_takeaway_types = {takeaway["type"] for takeaway in generated_takeaways}
    new_takeaway_types = generated_takeaway_types - existing_takeaway_types
    takeaway_types_to_create = []
    for takeaway_type in new_takeaway_types:
        takeaway_types_to_create.append(
            TakeawayType(name=takeaway_type, project=note.project)
        )
    TakeawayType.objects.bulk_create(takeaway_types_to_create)

    # Create takeaways
    takeaway_type_dict = {
        takeaway_type.name: takeaway_type
        for takeaway_type in TakeawayType.objects.filter(project=note.project)
    }
    takeaways_to_add = []
    note_takeaway_sequence = note.takeaway_sequence
    for generated_takeaway in generated_takeaways:
        note_takeaway_sequence += 1
        takeaways_to_add.append(
            Takeaway(
                title=generated_takeaway["title"],
                type=takeaway_type_dict[generated_takeaway["type"]],
                note=note,
                created_by=bot,
                code=f"{note.code}-{note_takeaway_sequence}",
            )
        )
    Takeaway.objects.bulk_create(takeaways_to_add)
    note.takeaway_sequence = note_takeaway_sequence
    note.save()
