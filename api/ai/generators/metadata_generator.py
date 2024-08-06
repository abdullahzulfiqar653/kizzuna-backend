from typing import Optional

import numpy as np
from django.utils.translation import gettext
from langchain.chains.combine_documents.map_reduce import (
    MapReduceDocumentsChain,
    ReduceDocumentsChain,
)
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.chains.openai_functions import create_structured_output_chain
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from langchain_openai.chat_models import ChatOpenAI
from pgvector.django import MaxInnerProduct
from pydantic import BaseModel, Field, StringConstraints
from typing_extensions import Annotated

from api.ai import config
from api.ai.embedder import embedder
from api.ai.generators.utils import token_tracker
from api.models.keyword import Keyword
from api.models.note import Note
from api.models.user import User


def get_chain():

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
    map_chain = LLMChain(llm=llm, prompt=map_prompt)

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
        meeting_type: str = Field(
            description=gettext(
                "The meeting type, which can be one of the following "
                "or any other meeting type that is appropriate: \n"
                "- User Interview\n"
                "- Sales Discovery Call\n"
                "- Customer Technical Demo Meeting\n"
                "- Requirement Gathering Meeting\n"
                "- Customer Check In\n"
                "- Quarterly Business Review (QBR)\n"
                "- Customer Kick-off Meeting\n"
                "- Customer Hand-off Meeting\n"
            )
        )
        summary: list[str] = Field(
            description=gettext("Summary of the text in point form.")
        )
        sentiment: Optional[Note.Sentiment] = Field(
            description=gettext("The sentiment of the text.")
        )
        keywords: list[Annotated[str, StringConstraints(max_length=50)]] = Field(
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
        MetadataSchema.model_json_schema(), llm, reduce_prompt
    )

    combine_documents_chain = StuffDocumentsChain(
        llm_chain=reduce_chain,
        document_prompt=document_prompt,
        document_variable_name=document_variable_name,
    )
    reduce_documents_chain = ReduceDocumentsChain(
        combine_documents_chain=combine_documents_chain,
    )
    map_reduce_chain = MapReduceDocumentsChain(
        llm_chain=map_chain,
        reduce_documents_chain=reduce_documents_chain,
    )
    return map_reduce_chain


def generate_metadata(note: Note, created_by: User):

    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    if note.media_type in ("audio", "video"):
        doc = Document(page_content=note.get_transcript_markdown())
    else:
        doc = Document(page_content=note.get_content_markdown())
    docs = text_splitter.split_documents([doc])

    map_reduce_chain = get_chain()
    with token_tracker(note.project, note, "generate-metadata", created_by):
        output = map_reduce_chain.invoke(docs)
    metadata = output["output_text"]

    # Map meeting type
    vector = embedder.embed_query(metadata["meeting_type"])
    blank_vector = embedder.embed_documents([""])[0]
    threshold = np.array(vector).dot(np.array(blank_vector))
    note_type = (
        note.project.note_types.annotate(score=-MaxInnerProduct("vector", vector))
        .filter(score__gt=threshold)
        .order_by("-score")
        .first()
    )

    note.title = metadata["title"]
    note.description = metadata["description"]
    note.type = note_type
    note.summary = metadata["summary"]
    note.sentiment = metadata.get("sentiment")
    note.save()

    existing_keywords = set(
        Keyword.objects.filter(name__in=metadata["keywords"]).values_list(
            "name", flat=True
        )
    )
    new_keywords = set(metadata["keywords"]) - existing_keywords
    if new_keywords:
        Keyword.objects.bulk_create([Keyword(name=keyword) for keyword in new_keywords])
    all_keywords = Keyword.objects.filter(name__in=metadata["keywords"])
    note.keywords.add(*all_keywords)
