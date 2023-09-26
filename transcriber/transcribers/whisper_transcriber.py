from faster_whisper import WhisperModel


class WhisperTranscriber:
    supported_filetypes = ['wav', 'mp3']

    def __init__(self):
        self.whisper = WhisperModel('base', device='cpu', compute_type='int8')

    def transcribe(self, filepath, filetype):
        if filetype not in self.supported_filetypes:
            raise ValueError(
                f'Filetype {filetype} not supported. '
                f'Supported file types are {self.supported_filetypes}.'
            )
        segments, _ = self.whisper.transcribe(filepath)
        transcript = ''.join([segment.text for segment in segments])
        return transcript
