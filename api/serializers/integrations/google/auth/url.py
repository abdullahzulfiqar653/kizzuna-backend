from rest_framework import serializers


class GoogleAuthUrlSerializer(serializers.Serializer):
    redirect_uri = serializers.URLField(read_only=True)
