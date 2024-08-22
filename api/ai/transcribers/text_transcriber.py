from api.utils.text import TextProcessor
from ..translator import google_translator
from .base_transcriber import BaseTranscriber
from django.core.files import File


class TextTranscriber(BaseTranscriber):
    supported_filetypes = ["txt"]
    translator = google_translator

    def transcribe(self, file: File, filetype: str, language: str) -> str:
        self.check_filetype(filetype)

        with file.open("r") as f:
            text = f.read().strip()

        return (
            TextProcessor(text)
            .truncate()
            .set_translator(self.translator)
            .translate(language)
        )


text_transcriber = TextTranscriber()
