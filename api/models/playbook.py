from django.db import models
from shortuuid.django_fields import ShortUUIDField
from api.utils import media
from api.models.user import User
from api.models.note import Note
from api.models.project import Project
from api.models.takeaway import Takeaway


class Playbook(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="playbooks"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="playbooks"
    )
    thumbnail = models.ImageField(upload_to="playbook/thumbnails/", null=True)
    video = models.FileField(
        upload_to="playbook/videos/",
        null=True,
        max_length=255,
    )
    video_size = models.PositiveIntegerField(
        null=True, help_text="File size measured in bytes."
    )
    thumbnail_size = models.PositiveIntegerField(
        null=True, help_text="Image size measured in bytes."
    )
    notes = models.ManyToManyField(Note, related_name="playbooks")
    takeaways = models.ManyToManyField(
        Takeaway, related_name="playbooks", through="PlaybookTakeaway"
    )

    def __str__(self):
        return self.title

    def create_playbook_clip_and_thumbnail(self):
        playbook_takeaways = self.playbook_takeaways.all().order_by("order")
        files = [pt.takeaway.highlight.clip for pt in playbook_takeaways]
        if files:
            video = media.merge_media_files(files)
            self.video = video
            self.thumbnail = media.create_thumbnail(files[0], 0)
            self.save()
        else:
            self.video = None
            self.save()

    def update_playbook_takeaway_times(self):
        playbook_takeaways = self.playbook_takeaways.all().order_by("order")
        start_time = 0
        updated_playbook_takeaways = []

        for pt in playbook_takeaways:
            highlight = pt.takeaway.highlight
            if highlight.start is not None and highlight.end is not None:
                duration = highlight.end - highlight.start
                pt.start = start_time
                pt.end = start_time + duration
                start_time = pt.end
                updated_playbook_takeaways.append(pt)
        playbook_takeaways.bulk_update(playbook_takeaways, ["start", "end"])
