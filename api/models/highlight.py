from django.db import models
from django.db.models import QuerySet

from api.models.takeaway import Takeaway


class Highlight(Takeaway):
    quote = models.CharField(max_length=1000)

    @classmethod
    def bulk_create(cls, objs):
        queryset = QuerySet(cls)
        queryset._for_write = True
        local_fields = cls._meta.local_fields
        return queryset._batched_insert(objs, local_fields, batch_size=None)
