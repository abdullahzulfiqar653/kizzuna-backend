from rest_framework import serializers


class GoogleAuthUrlSerializer(serializers.Serializer):
    authorization_url = serializers.URLField(read_only=True)
