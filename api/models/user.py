from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):
    skip_tutorial = models.BooleanField(default=False)
