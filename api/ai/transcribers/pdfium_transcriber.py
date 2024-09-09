from langchain_community.document_loaders.pdf import PyPDFium2Loader
from django.conf import settings
from django.core.files import File
from api.utils.text import TextProcessor

from ..translator import google_translator
from .base_transcriber import BaseTranscriber


class PDFiumTranscriber(BaseTranscriber):
    supported_filetypes = ["pdf"]
    translator = google_translator

    def transcribe(self, file: File, filetype: str, language: str) -> str:
        filepath = file.url if settings.USE_S3 else file.path
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
