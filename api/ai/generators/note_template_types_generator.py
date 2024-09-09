from textwrap import dedent
from pydantic.v1 import BaseModel
from langchain.schema.document import Document
from langchain.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from langchain.text_splitter import TokenTextSplitter
from langchain.output_parsers import PydanticOutputParser

from api.ai import config
from api.ai.translator import google_translator
from api.ai.generators.utils import ParserErrorCallbackHandler, token_tracker

from api.models.note import Note
from api.models.user import User
from api.models.note_template import NoteTemplate, default_templates
from api.models.note_template_type import NoteTemplateType


def get_template_type_chain(template_name, template_types):
    class TemplateTypeSchema(BaseModel):
        name: str
        data: str

    class TemplateTypesSchema(BaseModel):
        types: list[TemplateTypeSchema]

    system_prompt = dedent(
        """
            Your task is to analyze a meeting transcript and generate data for the given template and its types.

            Template Name: {{TEMPLATE_NAME}}

            Template Types:
            {{TEMPLATE_TYPES}}

            For each template type, generate the following:
            1. Extract the relevant data from the transcript based on the template and its types.
            2. For each template type, generate the corresponding data in text format.

            The output should be in the following JSON structure:
            {
                "types": [
                    {
                        "name": "<template type name>",
                        "data": "<generated data for this template type>"
                    },
                    {
                        // Additional types...
                    }
                ]
            }

            Only provide the generated data relevant to the template and its types.
            Ensure all quotes and information come directly from the transcript and are properly formatted.
        """
    )
    llm = ChatOpenAI(model=config.model)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("human", system_prompt),
        ],
        template_format="jinja2",
    )
    parser = PydanticOutputParser(pydantic_object=TemplateTypesSchema)
    chain = prompt | llm.bind(response_format={"type": "json_object"}) | parser
    return chain


def generate_template_types(note: Note, created_by: User):
    text_splitter = TokenTextSplitter(
        model_name=config.model,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    
    bot = User.objects.get(username="bot@raijin.ai")
    doc = Document(page_content=note.get_markdown())
    docs = text_splitter.split_documents([doc])

    note_templates_to_create = []
    generated_template_types = []
    for template in default_templates:
        note_template = NoteTemplate(note=note, name=template["name"])
        note_templates_to_create.append(note_template)
        with token_tracker(
            note.project,
            note,
            f'generate-template-types-{template["name"]}',
            created_by,
        ):
            outputs = [
                {
                    "output": get_template_type_chain(
                        template["name"], template["types"]
                    ).invoke(
                        {
                            "TEMPLATE_NAME": template["name"],
                            "TEMPLATE_TYPES": template["types"],
                            "TRANSCRIPT": doc.page_content,
                        },
                        config={"callbacks": [ParserErrorCallbackHandler()]},
                    ),
                }
                for doc in docs
            ]
        print(f"Outputs: {outputs}")
        if not outputs:
            continue

        generated_template_types.extend(
            [
                NoteTemplateType(
                    template=note_template,
                    name=google_translator.translate(
                        template_type["name"], note.project.language
                    ),
                    data=google_translator.translate(
                        template_type["data"], note.project.language
                    ),
                )
                for output in outputs
                for template_type in output["output"].dict()["types"]
            ]
        )
    NoteTemplate.objects.bulk_create(note_templates_to_create)
    NoteTemplateType.objects.bulk_create(generated_template_types)
