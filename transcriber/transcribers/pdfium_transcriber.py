from langchain.document_loaders import PyPDFium2Loader

from .base_transcriber import BaseTranscriber
from .google_translator import google_translator


class PDFiumTranscriber(BaseTranscriber):
    supported_filetypes = ['pdf']
    translator = google_translator

    def transcribe(self, filepath: str, filetype: str, language: str) -> str:
        self.check_filetype(filetype)
        documents = PyPDFium2Loader(filepath).load()
        text = '\n'.join([doc.page_content for doc in documents])
        return self.translator.translate(text, language)


pdfium_transcriber = PDFiumTranscriber()
