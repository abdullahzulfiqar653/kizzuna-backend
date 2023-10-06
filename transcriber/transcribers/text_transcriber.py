from transcriber.transcribers.base_transcriber import BaseTranscriber


class TextTranscriber(BaseTranscriber):
    supported_filetypes = ['txt']

    def transcribe(self, filepath: str, filetype: str) -> str:
        self.check_filetype(filetype)
        with open(filepath, 'r') as file:
            text = file.read()
        return text.strip()


text_transcriber = TextTranscriber()
