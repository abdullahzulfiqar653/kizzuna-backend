from django.db import models
from django.db.models import QuerySet

from api.models.takeaway import Takeaway


class Highlight(Takeaway):
    quote = models.CharField(max_length=1000)
    start = models.IntegerField(null=True)
    end = models.IntegerField(null=True)
    clip = models.FileField(upload_to="clips/", null=True)
    thumbnail = models.FileField(upload_to="thumbnails/", null=True)
    clip_size = models.PositiveIntegerField(
        null=True, help_text="File size measured in bytes."
    )
    thumbnail_size = models.PositiveIntegerField(
        null=True, help_text="File size measured in bytes."
    )

    @classmethod
    def bulk_create(cls, objs):
        queryset = QuerySet(cls)
        queryset._for_write = True
        local_fields = cls._meta.local_fields
        return queryset._batched_insert(objs, local_fields, batch_size=None)
