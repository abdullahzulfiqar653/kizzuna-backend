from django.db import models
from django.contrib.auth.models import User
from enum import Enum

class RoleEnum(Enum):
    ADMIN = 'admin'
    MANAGER = 'manager'
    EMPLOYEE = 'employee'

    def __str__(self):
        return self.value

class User(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birthday = models.DateField(null=True, blank=True)
    position = models.CharField(null=True, max_length=150)
    auth_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='users', null=True)
    role = models.CharField(max_length=20, choices=[(role.value, role.name) for role in RoleEnum], null=True, blank=True)
    last_active_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.position}"