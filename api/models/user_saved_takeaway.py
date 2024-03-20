from django.db import models

from api.models.takeaway import Takeaway
from api.models.user import User


class UserSavedTakeaway(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    takeaway = models.ForeignKey(Takeaway, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
