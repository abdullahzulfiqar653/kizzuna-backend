# note/serializers.py
from rest_framework import serializers

from auth.serializers import AuthUserSerializer
from note.models import Note
from tag.serializers import TagSerializer


class NoteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    content = serializers.CharField(read_only=True)
    summary = serializers.CharField(read_only=True)
    code = serializers.CharField(read_only=True)
    takeaway_count = serializers.IntegerField(read_only=True)
    participant_count = serializers.IntegerField(read_only=True)
    author = AuthUserSerializer(read_only=True)
    is_analyzing = serializers.BooleanField(read_only=True)
    file_type = serializers.CharField(read_only=True)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Note
        exclude = ['takeaway_sequence', 'user_participants', 'workspace', 'keywords']
