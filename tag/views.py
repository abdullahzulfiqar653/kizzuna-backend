from rest_framework import generics, status
from rest_framework.response import Response

from tag.models import Tag
from tag.serializers import TagSerializer

from .models import Tag
