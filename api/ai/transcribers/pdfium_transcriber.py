from langchain_community.document_loaders.pdf import PyPDFium2Loader

from api.utils.text import TextProcessor

from ..translator import google_translator
from .base_transcriber import BaseTranscriber


class PDFiumTranscriber(BaseTranscriber):
    supported_filetypes = ["pdf"]
    translator = google_translator

    def transcribe(self, filepath: str, filetype: str, language: str) -> str:
        self.check_filetype(filetype)
        documents = PyPDFium2Loader(filepath).load()
        text = "\n".join([doc.page_content for doc in documents])
        return (
            TextProcessor(text)
            .truncate()
            .set_translator(self.translator)
            .translate(language)
        )


pdfium_transcriber = PDFiumTranscriber()
