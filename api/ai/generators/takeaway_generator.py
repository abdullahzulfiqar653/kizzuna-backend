from pprint import pprint

from django.utils.translation import gettext
from langchain.chains.openai_functions import create_structured_output_chain
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from langchain_community.chat_models import ChatOpenAI
from pydantic import BaseModel, Field

from api.ai import config
from api.models.note import Note
from api.models.takeaway import Takeaway
from api.models.user import User


def generate_takeaways(note: Note):
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

    class TakeawaysSchema(BaseModel):
        takeaways: list[TakeawaySchema] = Field(
            description=gettext(
                "A list of ten to twenty important takeaways of the text."
            ),
            min_items=10,
            max_items=20,
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
    takeaways_chain = create_structured_output_chain(
        TakeawaysSchema.model_json_schema(), llm, prompt, verbose=True
    )

    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    bot = User.objects.get(username="bot@raijin.ai")
    doc = Document(page_content=note.get_content_text())
    docs = text_splitter.split_documents([doc])
    outputs = [takeaways_chain.invoke(doc.page_content) for doc in docs]
    pprint(outputs)
    output_takeaways = [
        f'{takeaway["topic"]} - {takeaway["title"]}: {takeaway["significance"]}'
        for output in outputs
        for takeaway in output["function"]["takeaways"]
    ]
    for takeaway_title in output_takeaways:
        takeaway = Takeaway(title=takeaway_title, note=note, created_by=bot)
        takeaway.save()
