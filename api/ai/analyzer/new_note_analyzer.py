from decimal import Decimal
from time import time

from django.utils import translation
from langchain.callbacks import get_openai_callback
from pydub.utils import mediainfo

from api.ai.downloaders.web_downloader import WebDownloader
from api.ai.downloaders.youtube_downloader import YoutubeDownloader
from api.ai.generators.metadata_generator import generate_metadata
from api.ai.generators.tag_generator import generate_tags
from api.ai.generators.takeaway_generator import generate_takeaways
from api.ai.transcribers import openai_transcriber, transcriber_router
from api.models.note import Note

transcriber = transcriber_router
youtube_downloader = YoutubeDownloader()
web_downloader = WebDownloader()


class NewNoteAnalyzer:
    def to_content_state(self, text):
        return {"blocks": [{"text": block} for block in text.split("\n")]}

    def transcribe(self, note):
        filepath = note.file.path
        filetype = note.file_type
        language = note.project.language
        transcript = transcriber.transcribe(filepath, filetype, language)
        if transcript is not None:
            note.content = self.to_content_state(transcript)
            note.save()

    def update_audio_filesize(self, note):
        if (
            openai_transcriber in transcriber.transcribers
            and note.file_type in openai_transcriber.supported_filetypes
        ):
            audio_info = mediainfo(note.file.path)
            note.file_duration_seconds = round(float(audio_info["duration"]))
            note.analyzing_cost += note.file_duration_seconds * Decimal("0.0001")
            note.save()

    def download(self, note):
        if youtube_downloader.is_youtube_link(note.url):
            content = youtube_downloader.download(note.url)
            note.content = self.to_content_state(content)
        else:
            note.content = web_downloader.download(note.url)
        note.save()

    def summarize(self, note):
        with get_openai_callback() as callback:
            generate_takeaways(note)
            generate_metadata(note)
            generate_tags(note)
            note.analyzing_tokens += callback.total_tokens
            note.analyzing_cost += Decimal(callback.total_cost)
        note.save()

    def analyze(self, note: Note):
        note.is_analyzing = True
        note.save()

        with translation.override(note.project.language):
            try:
                print("========> Start transcribing")
                start = time()
                if note.file:
                    self.transcribe(note)
                    self.update_audio_filesize(note)
                elif note.url:
                    self.download(note)
                end = time()
                print(f"Elapsed time: {end - start} seconds")
                print("========> Start summarizing")
                self.summarize(note)
                print("========> End analyzing")
            except Exception as e:
                import traceback

                traceback.print_exc()
