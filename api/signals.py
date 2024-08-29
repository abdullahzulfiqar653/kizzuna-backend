import os

from django.apps import apps
from django.core.management import call_command
from django.db.models import Count
from django.db.models.signals import m2m_changed, post_delete, post_migrate, pre_delete
from django.dispatch import receiver

from api.integrations.recall import recall
from api.models.keyword import Keyword
from api.models.note import Note
from api.models.organization import Organization
from api.models.project import Project
from api.models.tag import Tag
from api.models.takeaway import Takeaway


def cleanup_keywords():
    Keyword.objects.annotate(note_count=Count("notes")).filter(note_count=0).delete()


def cleanup_organizations():
    Organization.objects.annotate(note_count=Count("notes")).filter(
        note_count=0
    ).delete()


def cleanup_tags():
    Tag.objects.filter(takeaway_count=0).delete()


def cleanup_recall_bots(project):
    for bot in project.recall_bots.all():
        recall.v1.bot(bot.id).delete()


@receiver(m2m_changed, sender=Note.keywords.through)
def note_keywords_changed(sender, action, instance, reverse, pk_set, **kwargs):
    if action in ("post_remove", "post_clear"):
        cleanup_keywords()


@receiver(post_delete, sender=Note)
def post_delete_note(sender, instance, **kwargs):
    cleanup_keywords()
    cleanup_organizations()


@receiver(m2m_changed, sender=Takeaway.tags.through)
def takeaway_tags_changed(sender, action, instance, reverse, pk_set, **kwargs):
    if action in ("post_remove", "post_clear"):
        cleanup_tags()


@receiver(post_delete, sender=Takeaway)
def post_delete_takeaway(sender, instance, **kwargs):
    cleanup_tags()


@receiver(post_migrate, sender=apps.get_app_config("api"))
def load_data_from_fixture(sender, **kwargs):
    fixture_file = os.path.join("api", "fixtures", "features.json")
    call_command("loaddata", fixture_file, app_label="api")


@receiver(pre_delete, sender=Project)
def pre_delete_project(sender, instance, **kwargs):
    cleanup_recall_bots(instance)
