from django.db import models
from shortuuid.django_fields import ShortUUIDField

from api.models.user import User
from api.models.workspace import Workspace


class Project(models.Model):
    class Language(models.TextChoices):
        ENGLISH = "en"
        INDONESIAN = "id"
        JAPANESE = "ja"
        SPANISH = "es"
        ITALIAN = "it"
        PORTUGUESE = "pt"
        GERMAN = "de"
        POLISH = "pl"
        FRENCH = "fr"
        DUTCH = "nl"
        SWEDISH = "sv"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, related_name="projects")
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="projects"
    )
    language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.ENGLISH
    )
    summary = models.TextField(blank=True)
    key_themes = models.JSONField(default=list)

    objective = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name
