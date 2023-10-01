from textwrap import dedent

from langchain.chains import LLMChain, RefineDocumentsChain
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema.document import Document
from langchain.text_splitter import TokenTextSplitter
from pydantic import BaseModel, Field, constr

from note.models import Note


class NoteInsightSchema(BaseModel):
    summary: str = Field(description='Summary of the text.')
    keywords: list[constr(max_length=50)] = Field(description='The list of relevant keywords of the text.')
    takeaways: list[str] = Field(description='What are the main messages to take away from the text. Not more than 5 takeaways from the text.')
    sentiment: Note.Sentiment = Field(description='The sentiment of the text.')


class RefineSummarizer:
    
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
                Analyze the following text: {context}
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
                "Here's your first results: {prev_response}. "
                "Now add to it based on the following context: {context}"
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
        results = self.chain.run(docs)
        return self.output_parser.parse(results).dict()
