import mammoth

from api.utils.markdown import MarkdownProcessor

from ..translator import google_translator
from .base_transcriber import BaseTranscriber


class DocxTranscriber(BaseTranscriber):
    supported_filetypes = ["docx"]
    translator = google_translator

    def transcribe(self, filepath: str, filetype: str, language: str) -> str:
        self.check_filetype(filetype)
        with open(filepath, "rb") as file:
            markdown = mammoth.convert_to_markdown(file).value
            return (
                MarkdownProcessor(markdown)
                .truncate()
                .fix_links()
                .set_translator(self.translator)
                .translate(language)
            )


docx_transcriber = DocxTranscriber()
