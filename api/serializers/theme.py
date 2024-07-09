from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers

from api.models.block import Block
from api.models.theme import Theme


class ThemeSerializer(OrderedModelSerializer, serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)

    class Meta:
        model = Theme
        fields = [
            "id",
            "block",
            "title",
            "order",
        ]
        read_only_fields = ["block"]

    def create(self, validated_data):
        request = self.context["request"]
        if request.block.type != Block.Type.THEMES:
            raise serializers.ValidationError("The block type must be themes.")
        validated_data["block"] = request.block
        return super().create(validated_data)
