from django.db import models
from django.contrib.auth.models import User
from workspace.models import Workspace
from enum import Enum
from shortuuid.django_fields import ShortUUIDField

class StatusEnum(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'

    def __str__(self):
        return self.value

class Project(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=[(status.value, status.name) for status in StatusEnum], default=StatusEnum.ACTIVE.value)
    users = models.ManyToManyField(User, related_name='projects')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='projects')
    

    def __str__(self):
        return self.name