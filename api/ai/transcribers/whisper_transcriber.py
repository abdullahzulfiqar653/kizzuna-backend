from faster_whisper import WhisperModel

from api.utils.text import TextProcessor

from ..translator import google_translator
from .base_transcriber import BaseTranscriber


class WhisperTranscriber(BaseTranscriber):
    supported_filetypes = ["wav", "mp3"]
    translator = google_translator

    def __init__(self):
        self.whisper = WhisperModel("base", device="cpu", compute_type="int8")

    def transcribe(self, filepath, filetype, language):
        self.check_filetype(filetype)
        segments, _ = self.whisper.transcribe(audio=filepath, language=language)
        text = "".join([segment.text for segment in segments])
        return (
            TextProcessor(text)
            .truncate()
            .set_translator(self.translator)
            .translate(language)
        )


whisper_transcriber = WhisperTranscriber()
