from textwrap import dedent
from typing import Optional

from langchain.chains import LLMChain, RefineDocumentsChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from pydantic import BaseModel, Field, constr
from langchain.schema import OutputParserException

from note.models import Note


class NoteInsightSchema(BaseModel):
    summary: str = Field(description='Summary of the text.')
    keywords: list[constr(max_length=50)] = Field(description='The list of relevant keywords of the text.')
    takeaways: list[str] = Field(description='At least 10 key takeaways, which could be user pain points, suggestions, positive moment, risk or opportunity.')
    sentiment: Optional[Note.Sentiment] = Field(description='The sentiment of the text.')


class RefineSummarizer:

    RETRY_ATTEMPTS = 3
    
    def __init__(self):

        output_parser = PydanticOutputParser(pydantic_object=NoteInsightSchema)
        llm = ChatOpenAI(verbose=True)

        # document prompt
        document_prompt = PromptTemplate(
            input_variables=["page_content"],
            template="{page_content}"
        )
        document_variable_name = "context"

        # initial llm chain
        initial_prompt = PromptTemplate(
            input_variables=['context'],
            template=dedent("""
                text:
                {context}
                
                Analyze the text above.
                {format_instructions}
            """),
            partial_variables={
                'format_instructions': output_parser.get_format_instructions(),
            },
        )
        initial_llm_chain = LLMChain(llm=llm, prompt=initial_prompt, verbose=True)

        # refine llm chain
        initial_response_name = "prev_response"
        refine_prompt = PromptTemplate(
            input_variables=['prev_response', 'context'],
            template=dedent("""
                Previous response:
                {prev_response}

                Text:
                {context}

                Analyze the text above following the output schema
                and add to the previous response given above.
                {format_instructions}
            """),
            partial_variables={
                'format_instructions': output_parser.get_format_instructions(),
            },
        )
        refine_llm_chain = LLMChain(llm=llm, prompt=refine_prompt, verbose=True)

        # defining self attributes
        self.output_parser = output_parser

        self.chain = RefineDocumentsChain(
            initial_llm_chain=initial_llm_chain,
            refine_llm_chain=refine_llm_chain,
            document_prompt=document_prompt,
            document_variable_name=document_variable_name,
            initial_response_name=initial_response_name,
            verbose=True,
        )

        self.text_splitter = TokenTextSplitter(
            model_name='gpt-3.5-turbo', 
            chunk_size=1500, 
            chunk_overlap=100
        )

    def summarize(self, text):
        doc = Document(page_content=text)
        docs = self.text_splitter.split_documents([doc])

        for _ in range(self.RETRY_ATTEMPTS):
            try:
                results = self.chain.run(docs)
                print(results)
                return self.output_parser.parse(results).dict()
            except OutputParserException:
                pass
