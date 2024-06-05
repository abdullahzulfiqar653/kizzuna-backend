from rest_framework import serializers

from api.models.note_property import NoteProperty
from api.models.option import Option
from api.serializers.option import OptionSerializer
from api.serializers.property import PropertySerializer


class NotePropertySerializer(serializers.ModelSerializer):
    property = PropertySerializer(read_only=True)
    options = OptionSerializer(many=True, read_only=True)
    option_ids = serializers.PrimaryKeyRelatedField(
        source="options", queryset=Option.objects.all(), many=True, write_only=True
    )

    class Meta:
        model = NoteProperty
        fields = "__all__"
        extra_kwargs = {
            "number_value": {"normalize_output": True},
        }

    def save(self, **kwargs):
        return super().save(**kwargs)
