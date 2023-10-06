from rest_framework import serializers

from tag.models import Tag


class TagSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=50, validators=[]) # Remove the unique validator

    class Meta:
        model = Tag
        fields = ['id', 'name']

    def create(self, validated_data):
        instance, _ = Tag.objects.get_or_create(**validated_data)
        return instance
