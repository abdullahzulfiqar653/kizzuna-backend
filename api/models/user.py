from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

# Create your models here.


class CustomUserManager(UserManager):
    def get_by_natural_key(self, username: str | None):
        return self.get(username__iexact=username)


class User(AbstractUser):
    skip_tutorial = models.BooleanField(default=False)
    consent_given = models.BooleanField(default=False)
    objects = CustomUserManager()
