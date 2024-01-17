from .base_transcriber import BaseTranscriber
from .docx_transcriber import docx_transcriber
from .openai_transcriber import openai_transcriber
from .pdfium_transcriber import pdfium_transcriber
from .text_transcriber import text_transcriber


class TranscriberRouter(BaseTranscriber):
    transcribers: list[BaseTranscriber] = [
        openai_transcriber,
        pdfium_transcriber,
        docx_transcriber,
        text_transcriber,
    ]

    @property
    def supported_filetypes(self):
        return {
            filetype
            for transcriber in self.transcribers
            for filetype in transcriber.supported_filetypes
        }

    def transcribe(self, filepath: str, filetype: str, language: str) -> str:
        self.check_filetype(filetype)
        for transcriber in self.transcribers:
            if filetype in transcriber.supported_filetypes:
                return transcriber.transcribe(filepath, filetype, language)


transcriber_router = TranscriberRouter()
