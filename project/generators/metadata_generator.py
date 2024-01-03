from enum import Enum
from pprint import pprint
from typing import Optional

from django.utils.translation import gettext
from langchain.chains import (
    LLMChain,
    MapReduceDocumentsChain,
    ReduceDocumentsChain,
    StuffDocumentsChain,
)
from langchain.chains.openai_functions import create_structured_output_chain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from pydantic import BaseModel, Field, constr

from note.models import Note
from tag.models import Keyword

from . import config


def generate_metadata(note: Note):
    llm = ChatOpenAI(model=config.model)

    map_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext(
                    "You are a skilled professional known for "
                    "exceptional ability to summarize texts."
                ),
            ),
            (
                "human",
                gettext("Summarize the following text.") + "\n\n{text}",
            ),
        ]
    )
    map_chain = LLMChain(llm=llm, prompt=map_prompt, verbose=True)

    class MeetingType(Enum):
        user_interview = "User Interview"
        discovery_call = "Sales Discovery Call"
        demo_meeting = "Customer Technical Demo Meeting"
        requirement_meeting = "Requirement Gathering Meeting"
        customer_checkin = "Customer Check In"
        business_review = "Quarterly Business Review (QBR)"
        kickoff_meeting = "Customer Kick-off Meeting"
        handoff_meeting = "Customer Hand-off Meeting"

    class MetadataSchema(BaseModel):
        title: str = Field(
            description=gettext(
                "Title of the meeting. Should be concise but informative."
            )
        )
        description: str = Field(
            description=gettext(
                "A short paragraph describing what the meeting is about."
            )
        )
        meeting_type: MeetingType = Field(
            description=gettext("What is the meeting type?")
        )
        summary: str = Field(description=gettext("Summary of the text."))
        sentiment: Optional[Note.Sentiment] = Field(
            description=gettext("The sentiment of the text.")
        )
        keywords: list[constr(max_length=50)] = Field(
            description=gettext("The list of relevant keywords of the text.")
        )

    document_prompt = PromptTemplate(
        input_variables=["page_content"],
        template="{page_content}",
    )
    document_variable_name = "text"

    reduce_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext("Follow the function parameter schema strictly."),
            ),
            (
                "human",
                gettext("Extract data from the following summaries.") + "\n\n{text}",
            ),
        ]
    )
    reduce_chain = create_structured_output_chain(
        MetadataSchema.schema(), llm, reduce_prompt
    )

    combine_documents_chain = StuffDocumentsChain(
        llm_chain=reduce_chain,
        document_prompt=document_prompt,
        document_variable_name=document_variable_name,
    )
    reduce_documents_chain = ReduceDocumentsChain(
        combine_documents_chain=combine_documents_chain,
        verbose=True,
    )
    map_reduce_chain = MapReduceDocumentsChain(
        llm_chain=map_chain,
        reduce_documents_chain=reduce_documents_chain,
        verbose=True,
    )

    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    doc = Document(page_content=note.content)
    docs = text_splitter.split_documents([doc])

    output = map_reduce_chain.invoke(docs)
    pprint(output)
    metadata = output["output_text"]
    note.title = metadata["title"]
    note.description = metadata["description"]
    note.type = metadata["meeting_type"]
    note.summary = metadata["summary"]
    note.sentiment = metadata.get("sentiment")
    note.save()
    for keyword in metadata["keywords"]:
        keyword, is_created = Keyword.objects.get_or_create(name=keyword)
        note.keywords.add(keyword)
