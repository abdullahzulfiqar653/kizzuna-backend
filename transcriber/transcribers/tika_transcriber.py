from tika import parser
from .base_transcriber import BaseTranscriber


class TikaTranscriber(BaseTranscriber):
    supported_filetypes = ['pdf']

    def transcribe(self, filepath: str, filetype: str) -> str:
        self.check_filetype(filetype)
        return parser.from_file(filepath)['content'].strip()


tika_transcriber = TikaTranscriber()
