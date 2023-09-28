from django_filters import rest_framework as filters
from note.models import Note

class NoteFilter(filters.FilterSet):
    created_at = filters.DateFromToRangeFilter(field_name='created_at')

    class Meta:
        model = Note
        fields = ['author', 'created_at', 'company_name', 'revenue', 'sentiment']
