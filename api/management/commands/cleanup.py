from django.core.management.base import BaseCommand
from django.db.models import Count

from api.models.keyword import Keyword
from api.models.organization import Organization
from api.models.project import Project
from api.models.tag import Tag
from api.models.takeaway_type import TakeawayType
from api.models.workspace import Workspace


class Command(BaseCommand):
    help = "Clean up keywords, tags, workspace, projects."

    def handle(self, *args, **options):
        self.cleanup_projects()
        self.cleanup_workspaces()
        self.cleanup_keywords()
        self.cleanup_organizations()
        self.cleanup_tags()
        self.cleanup_takeaway_types()

    def cleanup_projects(self):
        Project.objects.annotate(user_count=Count("users")).filter(
            user_count=0
        ).delete()

    def cleanup_workspaces(self):
        Workspace.objects.annotate(member_count=Count("members")).filter(
            member_count=0
        ).delete()

    def cleanup_keywords(self):
        Keyword.objects.annotate(note_count=Count("notes")).filter(
            note_count=0
        ).delete()

    def cleanup_organizations(self):
        Organization.objects.annotate(note_count=Count("notes")).filter(
            note_count=0
        ).delete()

    def cleanup_tags(self):
        Tag.objects.filter(takeaway_count=0).delete()

    def cleanup_takeaway_types(self):
        TakeawayType.objects.annotate(takeaway_count=Count("takeaways")).filter(
            takeaway_count=0
        ).delete()
