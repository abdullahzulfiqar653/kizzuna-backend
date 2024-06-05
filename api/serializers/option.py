from ordered_model.serializers import OrderedModelSerializer
from rest_framework import serializers

from api.models.option import Option


class OptionSerializer(OrderedModelSerializer, serializers.ModelSerializer):
    order = serializers.IntegerField(required=False)

    class Meta:
        model = Option
        fields = "__all__"
