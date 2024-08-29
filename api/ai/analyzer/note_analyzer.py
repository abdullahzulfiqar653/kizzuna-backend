import os
from decimal import Decimal
from time import time
from urllib.parse import urlparse

from django.db.models import QuerySet
from django.utils import translation
from pydub.utils import mediainfo

from api.ai.downloaders.web_downloader import WebDownloader
from api.ai.downloaders.youtube_downloader import YoutubeDownloader
from api.ai.generators.metadata_generator import generate_metadata
from api.ai.generators.tag_generator import generate_tags
from api.ai.generators.task_generator import generate_tasks
from api.ai.generators.takeaway_generator import generate_takeaways
from api.ai.transcribers import assemblyai_transcriber
from api.ai.transcribers.transcriber_router import TranscriberRouter
from api.models.note import Note
from api.models.takeaway_type import TakeawayType
from api.models.usage.transciption import TranscriptionUsage
from api.models.user import User
from api.storage_backends import PrivateMediaStorage

youtube_downloader = YoutubeDownloader()
web_downloader = WebDownloader()


class NewNoteAnalyzer:
    transcriber_router = TranscriberRouter()

    def transcribe(self, note, created_by):
        if isinstance(note.file.storage, PrivateMediaStorage):
            self.transcribe_s3_file(note, created_by)
        else:
            self.transcribe_local_file(note, created_by)

    def transcribe_s3_file(self, note, created_by):
        filetype = os.path.splitext(urlparse(note.file.url).path)[1].strip(".")
        language = note.project.language
        filepath = note.file.url
        transcript = self.transcriber_router.transcribe(note.file, filetype, language)
        if transcript is not None:
            if self.transcriber_router.transcriber_used is assemblyai_transcriber:
                note.transcript = transcript.to_transcript()
            else:
                note.content = transcript.to_lexical()
            note.save()
        self.track_audio_filesize(note, filepath, created_by)

    def transcribe_local_file(self, note, created_by):
        filepath = note.file.path
        filetype = note.file_type
        language = note.project.language
        transcript = self.transcriber_router.transcribe(note.file, filetype, language)
        if transcript is not None:
            if self.transcriber_router.transcriber_used is assemblyai_transcriber:
                note.transcript = transcript.to_transcript()
            else:
                note.content = transcript.to_lexical()
            note.save()
        self.track_audio_filesize(note, filepath, created_by)

    def track_audio_filesize(self, note: Note, filepath: str, created_by: User):
        if self.transcriber_router.transcriber_used is assemblyai_transcriber:
            audio_info = mediainfo(filepath)
            duration_second = round(float(audio_info["duration"]))
            t = TranscriptionUsage.objects.create(
                workspace=note.project.workspace,
                project=note.project,
                note=note,
                created_by=created_by,
                value=duration_second,
                cost=Decimal("0.0001") * duration_second,
            )

    def download(self, note):
        if youtube_downloader.is_youtube_link(note.url):
            content = youtube_downloader.download(note.url)
        else:
            content = web_downloader.download(note.url)
        note.content = content.to_lexical()
        note.save()

    def analyze(self, note: Note, created_by: User):
        with translation.override(note.project.language):
            print("========> Start transcribing")
            start = time()
            if note.file:
                self.transcribe(note, created_by)
            elif note.url:
                self.download(note)
            end = time()
            print("========> Generating Tasks")
            generate_tasks(note, created_by)
            print(f"Elapsed time: {end - start} seconds")
            print("========> Generating metadata")
            generate_metadata(note, created_by)
            print("========> End analyzing")


class ExistingNoteAnalyzer(NewNoteAnalyzer):
    def analyze(
        self, note: Note, takeaway_types: QuerySet[TakeawayType], created_by: User
    ):
        with translation.override(note.project.language):
            print("========> Generating takeaways")
            generate_takeaways(note, takeaway_types, created_by)
            print("========> Generating tags")
            generate_tags(note, takeaway_types, created_by)
            print("========> End analyzing")
