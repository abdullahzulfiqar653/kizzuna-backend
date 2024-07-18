from textwrap import dedent

from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from api.models.note import Note
from api.models.user import User
from api.utils.lexical import LexicalProcessor


def generate_message(note: Note, created_by: User):
    # TODO: To handle the case where the prompt exceeds context window
    messages = note.messages.order_by("order")
    system_prompt = dedent(
        """
            You will be given a transcript and a user query. Your task is to generate a message that is relevant to the context of the transcript and responds to the user's query. If the user's query is not related to the given context, you should inform the user that their query is irrelevant to the provided context.

            Here is the transcript:
            <transcript>
            {transcript}
            </transcript>
        """
    )
    instruction_prompt = dedent(
        """
            Now, carefully analyze the transcript and keep its content in mind. You will use this information to respond to the user's query.

            When you receive a user query, follow these steps:
            1. Determine if the query is relevant to the context provided in the transcript.
            2. If the query is relevant:
                a. Generate a response that addresses the user's query using information from the transcript.
                b. Ensure your response is concise, informative, and directly related to the query and transcript content.
                c. Present the response in a readable format, using appropriate paragraphs, bullet points, or numbered lists if necessary.
            3. If the query is not relevant to the transcript:
                a. Inform the user that their query is not related to the given context.
                b. Politely suggest that they ask a question related to the information provided in the transcript.
        """
    )
    chat_history = [(message.role, message.text) for message in messages]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            *chat_history[:-1],
            ("human", instruction_prompt),
            chat_history[-1],
        ]
    )
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    chain = prompt | llm
    lexical = LexicalProcessor(note.content["root"])
    transcript = lexical.to_text()
    output = chain.invoke({"transcript": transcript})
    return output.content
