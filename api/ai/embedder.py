from langchain_openai import OpenAIEmbeddings

from . import config

embedder = OpenAIEmbeddings(model=config.embedding_model)
