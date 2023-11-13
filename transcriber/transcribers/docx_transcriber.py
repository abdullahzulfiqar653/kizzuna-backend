from docx import Document

from .base_transcriber import BaseTranscriber
from .google_translator import google_translator


class DocxTranscriber(BaseTranscriber):
    supported_filetypes = ['docx']
    translator = google_translator

    def transcribe(self, filepath: str, filetype: str, language:str) -> str:
        self.check_filetype(filetype)
        doc = Document(filepath)
        text = '\n'.join([para.text for para in doc.paragraphs])
        return self.translator.translate(text, language)


docx_transcriber = DocxTranscriber()
