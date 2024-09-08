from rest_framework import serializers
from api.models import NoteTemplateType


class NoteTemplateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteTemplateType
        fields = ["id", "name", "data"]
        read_only_fields = ["id"]
