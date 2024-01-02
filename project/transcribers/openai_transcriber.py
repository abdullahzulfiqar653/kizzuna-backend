import openai
from .base_transcriber import BaseTranscriber


class OpenAITranscriber(BaseTranscriber):
    supported_filetypes = ['flac', 'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'ogg', 'wav', 'webm']

    def transcribe(self, filepath, filetype, language):
        self.check_filetype(filetype)
        with open(filepath, 'rb') as audio_file:
            transcript = openai.Audio.transcribe(
                model='whisper-1',
                file=audio_file,
                response_format='verbose_json',
                language=language,
            )
        print('Transcript duration:', transcript['duration'])
        return transcript['text']


openai_transcriber = OpenAITranscriber()
