from django.core.exceptions import ValidationError
from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.highlight import Highlight
from api.models.keyword import Keyword
from api.models.note_type import NoteType
from api.models.organization import Organization
from api.models.project import Project
from api.models.user import User
from api.models.workspace import Workspace
from api.utils.assembly import AssemblyProcessor, blank_transcript
from api.utils.lexical import LexicalProcessor, blank_content


def validate_file_size(value):
    max_size = 30 * 1024 * 1024  # 30 MB
    if value.size > max_size:
        raise ValidationError("File size cannot exceed 20 MB.")


def validate_file_type(value):
    allowed_extensions = [filetype[0] for filetype in Note.FileType.choices]
    ext = value.name.split(".")[-1]
    if ext.lower() not in allowed_extensions:
        raise ValidationError(f"Only {allowed_extensions} files are allowed.")


class Note(models.Model):
    class Revenue(models.TextChoices):
        LOW = "Low"
        MEDIUM = "Medium"
        HIGH = "High"

    class FileType(models.TextChoices):
        DOCX = "docx"
        FLAC = "flac"
        MP3 = "mp3"
        MP4 = "mp4"
        PDF = "pdf"
        TXT = "txt"
        WAV = "wav"
        M4A = "m4a"

    class MediaType(models.TextChoices):
        AUDIO = "audio"
        VIDEO = "video"
        TEXT = "text"
        UNKNOWN = "unknown"

    class Sentiment(models.TextChoices):
        POSITIVE = "Positive"
        NEUTRAL = "Neutral"
        NEGATIVE = "Negative"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="notes")
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="notes"
    )
    organizations = models.ManyToManyField(Organization, related_name="notes")
    revenue = models.CharField(max_length=6, choices=Revenue.choices, null=True)
    description = models.TextField()
    type = models.ForeignKey(
        NoteType, on_delete=models.SET_NULL, related_name="notes", null=True
    )

    url = models.URLField(max_length=255, null=True)
    file = models.FileField(
        upload_to="attachments/",
        validators=[validate_file_size, validate_file_type],
        null=True,
        max_length=255,
    )
    file_type = models.CharField(max_length=4, choices=FileType.choices, null=True)
    file_size = models.IntegerField(null=True, help_text="File size measured in bytes.")
    google_drive_file_timestamp = models.DateTimeField(null=True)
    is_analyzing = models.BooleanField(default=False)
    is_auto_tagged = models.BooleanField(default=False)
    content = models.JSONField(default=blank_content)
    transcript = models.JSONField(default=blank_transcript)
    summary = models.JSONField(default=list)
    keywords = models.ManyToManyField(Keyword, related_name="notes")
    sentiment = models.CharField(max_length=8, choices=Sentiment.choices, null=True)

    # Slack Integration
    slack_channel_id = models.CharField(max_length=25, null=True)
    slack_team_id = models.CharField(max_length=25, null=True)

    def __str__(self):
        return self.title

    @property
    def highlights(self):
        return Highlight.objects.filter(note=self)

    def save(self, *args, **kwargs):
        if self.file and self.file.name:
            self.file_type = self.file.name.split(".")[-1].lower()
        else:
            self.file_type = None
        self.workspace = self.project.workspace
        super().save(*args, **kwargs)

    @property
    def media_type(self) -> MediaType:
        # Mapping of file types to media types
        to_media_type = {
            "flac": Note.MediaType.AUDIO,
            "mp3": Note.MediaType.AUDIO,
            "mp4": Note.MediaType.VIDEO,
            "mpga": Note.MediaType.AUDIO,
            "m4a": Note.MediaType.AUDIO,
            "ogg": Note.MediaType.AUDIO,
            "wav": Note.MediaType.AUDIO,
            "webm": Note.MediaType.VIDEO,
            "docx": Note.MediaType.TEXT,
            "pdf": Note.MediaType.TEXT,
            "txt": Note.MediaType.TEXT,
        }

        # Return the media type based on the file type
        return to_media_type.get(self.file_type, Note.MediaType.UNKNOWN)

    def get_markdown(self):
        if self.media_type in {Note.MediaType.AUDIO, Note.MediaType.VIDEO}:
            assembly = AssemblyProcessor(self.transcript)
            return assembly.to_markdown()
        else:  # Note.MediaType.TEXT or Note.MediaType.UNKNOWN
            lexical = LexicalProcessor(self.content["root"])
            return lexical.to_markdown()
