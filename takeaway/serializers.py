from collections import OrderedDict

from rest_framework import serializers

from tag.serializers import TagSerializer
from user.serializers import AuthUserSerializer

from .models import Takeaway


class TakeawaySerializer(serializers.ModelSerializer):
    created_by = AuthUserSerializer(read_only=True)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Takeaway
        fields = [
            'id',
            'title',
            'tags',
            'description',
            'status',
            'note',
            'created_by',
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['created_by'] is None:
            data['created_by'] = OrderedDict({
                'username': '',
                'first_name': 'Created by AI',
                'last_name': ''
            })
        return data
