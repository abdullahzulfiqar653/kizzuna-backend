from typing import Any

import markdown
from html_to_draftjs import html_to_draftjs
from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import Html2TextTransformer


class WebDownloader:
    def download(self, url: str) -> dict[str, Any]:
        loader = AsyncChromiumLoader([url])
        docs = loader.load()

        html2text = Html2TextTransformer()
        docs_transformed = html2text.transform_documents(docs)
        markdown_string = docs_transformed[0].page_content

        html_string = markdown.markdown(markdown_string)
        content_state = html_to_draftjs(html_string)

        return content_state


__all__ = ["WebDownloader"]
