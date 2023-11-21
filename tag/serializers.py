from rest_framework import serializers

from tag.models import Keyword, Tag


class TagSerializer(serializers.ModelSerializer):
    takeaway_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ["id", "name", "project", "takeaway_count"]
        validators = []  # To skip unique together constraint

    def create(self, validated_data):
        instance, _ = Tag.objects.get_or_create(**validated_data)
        return instance


class KeywordSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(
        max_length=50, validators=[]  # Remove the unique validator
    )

    class Meta:
        model = Keyword
        fields = ["id", "name"]

    def create(self, validated_data):
        instance, _ = Keyword.objects.get_or_create(**validated_data)
        return instance
