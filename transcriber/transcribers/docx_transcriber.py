from .base_transcriber import BaseTranscriber
from docx import Document


class DocxTranscriber(BaseTranscriber):
    supported_filetypes = ['docx']

    def transcribe(self, filepath: str, filetype: str) -> str:
        self.check_filetype(filetype)
        doc = Document(filepath)
        return '\n'.join([para.text for para in doc.paragraphs])


docx_transcriber = DocxTranscriber()
