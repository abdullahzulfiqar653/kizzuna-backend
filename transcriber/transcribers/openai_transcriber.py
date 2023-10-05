import openai


class OpenAITranscriber:
    supported_filetypes = ['flac', 'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'ogg', 'wav', 'webm']

    def transcribe(self, filepath, filetype):
        if filetype not in self.supported_filetypes:
            raise ValueError(
                f'Filetype {filetype} not supported. '
                f'Supported file types are {self.supported_filetypes}.'
            )
        with open(filepath, 'rb') as audio_file:
            transcript = openai.Audio.transcribe(
                model='whisper-1', 
                file=audio_file, 
                response_format='verbose_json',
                language='en',
            )
        print('Transcript duration:', transcript['duration'])
        return transcript['text']
