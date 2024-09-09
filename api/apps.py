from pathlib import Path

from django.apps import AppConfig
from django.conf import settings
from django.utils import autoreload


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"

    def add_extra_files(self, sender: autoreload.StatReloader, **kwargs):
        # Add .env file to extra_files to trigger autoreload on .env changes
        sender.extra_files.update([Path(__file__).parents[1] / ".env"])

    def ready(self):
        from . import signals  # This is needed to import signals

        if settings.DEBUG:
            autoreload.autoreload_started.connect(self.add_extra_files)
