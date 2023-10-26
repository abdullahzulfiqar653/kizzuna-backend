from collections import OrderedDict

from rest_framework import exceptions, serializers
from rest_framework.fields import empty

from note.models import Note
from tag.serializers import TagSerializer
from user.serializers import AuthUserSerializer

from .models import Highlight, Takeaway


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
            'created_by',
        ]

    def create(self, validated_data):
        report_id = self.context['view'].kwargs['report_id']
        request = self.context['request']
        note = Note.objects.filter(id=report_id).first()
        if note is None or not note.project.users.contains(request.user):
            exceptions.NotFound('Report is not found.')
        
        validated_data['created_by'] = request.user
        validated_data['note'] = note
        return super().create(validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('created_by') is None:
            data['created_by'] = OrderedDict({
                'username': '',
                'first_name': 'Created by AI',
                'last_name': ''
            })
        return data


class HighlightSerializer(TakeawaySerializer):

    class Meta:
        model = Highlight
        fields = [
            'id',
            'start',
            'end',
        ]

    def validate(self, data):
        start = data['start']
        end = data['end']
        if not (0 <= start < end):
            raise serializers.ValidationError(
                "start and end must satisfy the condition: "
                "0 <= start < end."
            )
        return super().validate(data)
        
    def create(self, validated_data):
        report_id = self.context['view'].kwargs['report_id']
        note = Note.objects.filter(id=report_id).first()
        request = self.context['request']
        if note is None or not note.project.users.contains(request.user):
            exceptions.NotFound('Report is not found.')

        request = self.context['request']
        validated_data['created_by'] = request.user
        validated_data['note'] = note
        return super().create(validated_data)

    def to_representation(self, instance):
        # Overwriting TakeawaySerializer.to_representation with rest_framework original function
        return super(TakeawaySerializer, self).to_representation(instance)
    