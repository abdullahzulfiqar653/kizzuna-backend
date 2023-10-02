from django_filters import rest_framework as filters
from note.models import Note

class NoteFilter(filters.FilterSet):
    company_name = filters.CharFilter(lookup_expr='icontains')
    author = filters.CharFilter(field_name='author__username')
    created_at = filters.DateFromToRangeFilter(field_name='created_at')

    class Meta:
        model = Note
        fields = ['author', 'created_at', 'company_name', 'revenue', 'sentiment']
