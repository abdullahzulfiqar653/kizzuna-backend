import mammoth
from django.core.files import File

from api.utils.markdown import MarkdownProcessor
from ..translator import google_translator
from .base_transcriber import BaseTranscriber


class DocxTranscriber(BaseTranscriber):
    supported_filetypes = ["docx"]
    translator = google_translator

    def transcribe(self, file: File, filetype: str, language: str) -> str:
        self.check_filetype(filetype)

        with file.open("rb") as f:
            markdown = mammoth.convert_to_markdown(f).value

        return (
            MarkdownProcessor(markdown)
            .truncate()
            .fix_links()
            .set_translator(self.translator)
            .translate(language)
        )


docx_transcriber = DocxTranscriber()
