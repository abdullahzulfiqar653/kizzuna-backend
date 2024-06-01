from api.utils.text import TextProcessor

from ..translator import google_translator
from .base_transcriber import BaseTranscriber


class TextTranscriber(BaseTranscriber):
    supported_filetypes = ["txt"]
    translator = google_translator

    def transcribe(self, filepath: str, filetype: str, language: str) -> str:
        self.check_filetype(filetype)
        with open(filepath, "r") as file:
            text = file.read().strip()
        return (
            TextProcessor(text)
            .truncate()
            .set_translator(self.translator)
            .translate(language)
        )


text_transcriber = TextTranscriber()
