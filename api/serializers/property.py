from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers

from api.models.property import Property


def find_unique_name(base_name, existing_names):
    name = base_name
    counter = 2
    while name in existing_names:
        name = f"{base_name} {counter}"
        counter += 1
    return name


class PropertySerializer(OrderedModelSerializer, serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)

    class Meta:
        model = Property
        fields = "__all__"
        extra_kwargs = {"name": {"required": False}}

    def create(self, validated_data):
        if validated_data.get("name") is None:
            base_name = validated_data.get("data_type")
            request = self.context["request"]
            existing_names = set(
                request.project.properties.values_list("name", flat=True)
            )
            validated_data["name"] = find_unique_name(base_name, existing_names)
        return super().create(validated_data)
