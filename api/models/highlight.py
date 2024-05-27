from django.db import models

from api.models.takeaway import Takeaway


class Highlight(Takeaway):
    quote = models.CharField(max_length=1000)
