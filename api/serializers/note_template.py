from rest_framework import serializers
from api.models.note_template import NoteTemplate
from api.serializers.note_template_type import NoteTemplateTypeSerializer


class NoteTemplateSerializer(serializers.ModelSerializer):
    types = NoteTemplateTypeSerializer(many=True, read_only=True)

    class Meta:
        model = NoteTemplate
        fields = ["id", "name", "types"]
        read_only_fields = ["id"]
