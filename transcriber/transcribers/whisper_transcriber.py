from faster_whisper import WhisperModel

from transcriber.transcribers.base_transcriber import BaseTranscriber


class WhisperTranscriber(BaseTranscriber):
    supported_filetypes = ['wav', 'mp3']

    def __init__(self):
        self.whisper = WhisperModel('base', device='cpu', compute_type='int8')

    def transcribe(self, filepath, filetype):
        self.check_filetype(filetype)
        segments, _ = self.whisper.transcribe(filepath)
        transcript = ''.join([segment.text for segment in segments])
        return transcript


whisper_transcriber = WhisperTranscriber()
