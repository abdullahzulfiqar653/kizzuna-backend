import time
import assemblyai as aai
from django.conf import settings
from api.utils.assembly import AssemblyProcessor
from .base_transcriber import BaseTranscriber

aai.settings.api_key = settings.ASSEMBLY_AI_API_KEY


class AssemblyAITranscriber(BaseTranscriber):
    """
    Built by AI experts, AssemblyAI's Speech AI models include accurate speech-to-text for voice
    data (such as calls, virtual meetings, and podcasts), speaker detection, sentiment analysis,
    chapter detection, PII redaction, and more.
    """

    supported_filetypes = [
        "flac",
        "mp3",
        "mp4",
        "mpga",
        "m4a",
        "ogg",
        "wav",
        "webm",
    ]

    def transcribe(self, filepath, filetype, language):
        self.check_filetype(filetype)
        with open(filepath, "rb") as audio_file:
            config = aai.TranscriptionConfig(
                speaker_labels=True,
            )
            start_time = time.time()
            transcript = aai.Transcriber().transcribe(audio_file, config)
            end_time = time.time()
        print(f"Transcript duration: {end_time - start_time}")
        return AssemblyProcessor(transcript.json_response)


assemblyai_transcriber = AssemblyAITranscriber()
