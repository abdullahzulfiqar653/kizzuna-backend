from rest_framework import serializers

from tag.models import Tag


class TagSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'name']
