import json

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
from api.models.takeaway_type import TakeawayType
from api.models.user import User


def get_chain():
    class TakeawaySchema(BaseModel):
        "The takeaway extracted from the text targeted for a specific question."

        question_id: str = Field(
            description=gettext(
                "The id of the question the takeaway is for."
                "For example: '5R4koV7RvP2D'."
            )
        )
        topic: str = Field(
            description=gettext("Topic of the takeaway, for grouping the takeaways.")
        )
        title: str = Field(
            description=gettext(
                "What the takeaway is about. "
                "This should be an important message of the text "
                "carrying a single idea."
            )
        )
        significance: str = Field(
            description=gettext("The reason why the takeaway is important.")
        )
        type: str = Field(
            description=gettext(
                "The takeaway type. For example: 'Pain Point', 'Moment of Delight', "
                "'Pricing', 'Feature Request', 'Moment of Dissatisfaction', "
                "'Usability Issue', or any other issue types deemed logical."
            )
        )

    class TakeawaysSchema(BaseModel):
        "A list of extracted takeaways."

        takeaways: list[TakeawaySchema] = Field(
            description=gettext("A list of takeaways extracted from the text.")
        )

    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                gettext(
                    "Extract the takeaways for each question from the text. "
                    "There can be multiple takeaways for each question."
                ),
            ),
            (
                "human",
                gettext("Questions: {questions}\n\nText: \n{text}"),
            ),
        ]
    )
    takeaways_chain = create_structured_output_chain(
        TakeawaysSchema.model_json_schema(), llm, prompt
    )
    return takeaways_chain


def generate_takeaways_with_questions(note: Note):
    takeaways_chain = get_chain()

    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    bot = User.objects.get(username="bot@raijin.ai")
    doc = Document(page_content=note.get_content_text())
    docs = text_splitter.split_documents([doc])

    questions = [
        {"id": question.id, "question": question.title}
        for question in note.questions.all()
    ]
    questions_string = json.dumps(questions)

    outputs = [
        takeaways_chain.invoke(
            {"text": doc.page_content, "questions": questions_string}
        )
        for doc in docs
    ]

    generated_takeaways = [
        {
            "title": f'{takeaway["topic"]} - {takeaway["title"]}: {takeaway["significance"]}',
            "type": takeaway["type"],
            "question_id": takeaway["question_id"],
        }
        for output in outputs
        for takeaway in output["function"]["takeaways"]
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
                question_id=generated_takeaway["question_id"],
                code=f"{note.code}-{note_takeaway_sequence}",
            )
        )
    Takeaway.objects.bulk_create(takeaways_to_add)
    note.takeaway_sequence = note_takeaway_sequence
    note.save()
