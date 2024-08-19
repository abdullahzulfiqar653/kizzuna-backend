from django.db import models
from api.utils import media
from api.models.playbook import PlayBook
from api.models.takeaway import Takeaway
from ordered_model.models import OrderedModel


class PlayBookTakeaway(OrderedModel):
    playbook = models.ForeignKey(
        PlayBook, on_delete=models.CASCADE, related_name="playbook_takeaways"
    )
    takeaway = models.ForeignKey(Takeaway, on_delete=models.CASCADE)
    start = models.PositiveIntegerField(null=True)
    end = models.PositiveIntegerField(null=True)

    class Meta:
        ordering = ["order"]
        unique_together = ("playbook", "takeaway")

    def create_playbook_clip_and_thumbnail(self):
        files = [
            pt.takeaway.highlight.clip
            for pt in self.playbook.playbook_takeaways.all().order_by("order")
        ]
        if files:
            clip = media.merge_media_files(files)
            self.playbook.clip = clip
            self.playbook.save()
            self.playbook.thumbnail = media.create_thumbnail(self.playbook.clip, 1)
            self.playbook.save()
        else:
            self.playbook.clip = None
            self.playbook.save()

    def update_playbook_takeaway_times(self):
        playbook_takeaways = self.playbook.playbook_takeaways.all().order_by("order")
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
        PlayBookTakeaway.objects.bulk_update(playbook_takeaways, ["start", "end"])
