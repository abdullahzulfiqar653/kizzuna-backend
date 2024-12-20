from django.utils.translation import gettext
from langchain.prompts import ChatPromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from tiktoken import encoding_for_model

from api.ai import config


class Paragrapher:
    def paragraphing(self, segments: list) -> str:
        encoder = encoding_for_model(config.model)
        chain = self.get_paragraphing_chain()
        current_chunk_size = 0
        chunk = []
        paragraphs = []
        for segment in segments:
            segment_size = len(encoder.encode(segment))
            if current_chunk_size + segment_size < config.chunk_size:
                current_chunk_size += segment_size
                chunk.append(segment)
            else:
                message = chain.invoke({"text": " ".join(chunk).strip()})
                splitted = message.content.split("\n\n")
                paragraphs.extend(splitted[:-1])
                remain = splitted[-1]
                current_chunk_size = len(encoder.encode(remain)) + segment_size
                chunk = [remain, segment]
        message = chain.invoke({"text": " ".join(chunk).strip()})
        splitted = message.content.split("\n\n")
        paragraphs.extend(splitted)
        return "\n".join(paragraphs)

    def get_paragraphing_chain(self):
        llm = ChatOpenAI(model=config.model)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    gettext(
                        "Break the below text into paragraphs, "
                        "and follow identically the words that were given - "
                        "the only thing that should change is the paragraph breaks"
                    ),
                ),
                ("human", "{text}"),
            ]
        )
        chain = prompt | llm
        return chain
