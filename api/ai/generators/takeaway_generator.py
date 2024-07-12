import json
from textwrap import dedent

from django.db.models import QuerySet
from django.utils.translation import gettext
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from langchain_openai.chat_models import ChatOpenAI
from nltk.tokenize import sent_tokenize
from pydantic.v1 import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer

from api.ai import config
from api.ai.embedder import embedder
from api.ai.generators.utils import ParserErrorCallbackHandler, token_tracker
from api.ai.translator import google_translator
from api.models.highlight import Highlight
from api.models.note import Note
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User
from api.utils.lexical import LexicalProcessor


def get_chain(takeaway_type: TakeawayType):
    system_prompt = dedent(
        """Extract highly impactful {takeaway_type_name} from the source below.

        Separate different ideas into each {takeaway_type_name},
        each {takeaway_type_name} should convey a single idea only.

        Each {takeaway_type_name} should contain a topic, an insight,
        the significance of the takeaway, and the takeaway type.

        Give your output solely from information extracted from user given text.

        Generate JSON data according to the following schema:


        Schema:

        {schema}


        For example, the output should be the following:

        {example}"""
    )

    class TakeawaySchema(BaseModel):
        f"The {takeaway_type.name} extracted from the source.",

        topic: str = Field(
            description=f"Topic of the {takeaway_type.name} for grouping."
        )
        insight: str = Field(
            description=f"The {takeaway_type.name} - {takeaway_type.definition}."
        )
        significance: str = Field(
            description=(
                f"Give robust reason to your inference as to why the {takeaway_type.name} is important, "
                "based on the severity of the language used, how much it was stressed, and/or the frequency of this is mentioned."
            )
        )
        quote: str = Field(
            description=f"The verbatim quote from the source that supports the {takeaway_type.name}."
        )

    class TakeawaysSchema(BaseModel):
        "A list of extracted takeaways."

        takeaways: list[TakeawaySchema] = Field(
            description=f"A list of {takeaway_type.name} extracted from the text."
        )

    schema = TakeawaysSchema.schema_json().replace("{", "{{").replace("}", "}}")
    example = (
        json.dumps(
            {
                "takeaways": [
                    {
                        "topic": "Poor Onboarding Experience",
                        "insight": "This user complains that the onboarding and setup experience is terrible and does not know how to get to the core value of the software",
                        "significance": "[The significance of the takeaway]",
                    },
                    {
                        "topic": "Automated User Research and Automated Tagging",
                        "insight": "This user was delighted that the software automated away all of their manual tasks for user research when it automatically tagged all the notes that the user created",
                        "significance": "[The significance of the takeaway]",
                    },
                    {
                        "topic": "Not doing enough user interviews",
                        "insight": "[User's name] mentioned that they would like to be able to do more interviews on their customer brands and investigate what are their problems. This would then allow them to identify problem statements that they can solve for their customer brands",
                        "significance": "[The significance of the takeaway]",
                    },
                ]
            },
            indent=2,
        )
        .replace("{", "{{")
        .replace("}", "}}")
    )

    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext(
                    system_prompt.format(
                        schema=schema,
                        example=example,
                        takeaway_type_name=takeaway_type.name,
                    )
                ),
            ),
            (
                "human",
                gettext("\nSource: \n{source}"),
            ),
        ]
    )
    parser = PydanticOutputParser(pydantic_object=TakeawaysSchema)
    chain = prompt | llm.bind(response_format={"type": "json_object"}) | parser
    return chain


def generate_takeaways(
    note: Note, takeaway_types: QuerySet[TakeawayType], created_by: User
):
    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    bot = User.objects.get(username="bot@raijin.ai")
    doc = Document(page_content=note.get_content_markdown())
    docs = text_splitter.split_documents([doc])

    with token_tracker(note.project, note, "generate-takeaways", created_by):
        outputs = [
            {
                "takeaway_type": takeaway_type,
                "output": get_chain(takeaway_type).invoke(
                    {"source": doc.page_content},
                    config={"callbacks": [ParserErrorCallbackHandler()]},
                ),
            }
            for takeaway_type in takeaway_types
            for doc in docs
        ]

    generated_takeaways = [
        {
            "title": google_translator.translate(
                f'Topic: {takeaway["topic"]} - {takeaway["insight"].rstrip(".")}: {takeaway["significance"]}',
                note.project.language,
            ),
            "quote": takeaway["quote"],
            "takeaway_type": output["takeaway_type"],
        }
        for output in outputs
        for takeaway in output["output"].dict()["takeaways"]
    ]

    # Embed note content
    lexical = LexicalProcessor(note.content["root"])
    sentences = [
        sentence.strip()
        for paragraph in lexical.to_text().split("\n")
        for sentence in sent_tokenize(paragraph)
        if sentence.strip()  # Check if there is some text after stripping
    ]
    bi_sentences = [
        f"{sentence1} {sentence2}"
        for sentence1, sentence2 in zip(sentences[:-1], sentences[1:])
    ]
    tri_sentences = [
        f"{sentence1} {sentence2} {sentence3}"
        for sentence1, sentence2, sentence3 in zip(
            sentences[:-2], sentences[1:-1], sentences[2:]
        )
    ]
    sentences.extend(bi_sentences)
    sentences.extend(tri_sentences)
    vectorizer = TfidfVectorizer()
    doc_vecs = vectorizer.fit_transform(sentences)

    # Find best matches
    generated_takeaway_quotes = [takeaway["quote"] for takeaway in generated_takeaways]
    quote_vectors = vectorizer.transform(generated_takeaway_quotes)
    cosine_similarities = quote_vectors.dot(doc_vecs.T)
    best_matches = cosine_similarities.argmax(axis=1).A1

    # Embed generated takeaways
    generated_takeaway_titles = [takeaway["title"] for takeaway in generated_takeaways]
    generated_takeaway_vectors = embedder.embed_documents(generated_takeaway_titles)

    # Create takeaways
    takeaways_to_create = []
    highlights_to_create = []
    for generated_takeaway, vector, index in zip(
        generated_takeaways, generated_takeaway_vectors, best_matches
    ):

        takeaway = Takeaway(
            title=generated_takeaway["title"],
            vector=vector,
            note=note,
            created_by=bot,
            type=generated_takeaway["takeaway_type"],
        )

        highlight_str = sentences[index]
        lexical.highlight(highlight_str, takeaway.id)
        highlight = Highlight(takeaway_ptr_id=takeaway.id, quote=highlight_str)

        takeaways_to_create.append(takeaway)
        highlights_to_create.append(highlight)

    Takeaway.objects.bulk_create(takeaways_to_create)
    Highlight.bulk_create(highlights_to_create)

    # Update note.content
    note.save()
