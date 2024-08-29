from rest_framework import serializers

from api.models.note_property import NoteProperty
from api.models.option import Option
from api.serializers.option import OptionSerializer
from api.serializers.property import PropertySerializer


class NotePropertySerializer(serializers.ModelSerializer):
    property = PropertySerializer(read_only=True)
    options = OptionSerializer(many=True, read_only=True)
    option_ids = serializers.PrimaryKeyRelatedField(
        source="options", queryset=Option.objects.none(), many=True, write_only=True
    )

    def __init__(self, *args, **kwargs):
        # We set the queryset for the option_ids only after getting the instance
        super().__init__(*args, **kwargs)
        if self.instance and isinstance(self.instance, NoteProperty):
            self.fields["option_ids"].child_relation.queryset = (
                self.instance.property.options.all()
            )

    class Meta:
        model = NoteProperty
        fields = "__all__"
        extra_kwargs = {
            "number_value": {"normalize_output": True},
        }
