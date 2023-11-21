from django.apps import AppConfig
from django.db.models.signals import m2m_changed


class TakeawayConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "takeaway"

    def ready(self):
        from . import signals

        Takeaway = self.get_model("Takeaway")
        m2m_changed.connect(signals.takeaway_tags_changed, Takeaway.tags.through)
