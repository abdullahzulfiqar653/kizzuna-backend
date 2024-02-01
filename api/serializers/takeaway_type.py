from rest_framework import serializers

from api.models.takeaway_type import TakeawayType


class TakeawayTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TakeawayType
        fields = ["id", "name", "project"]
