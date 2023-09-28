from django_filters import rest_framework as filters
from takeaway.models import Takeaway

class TakeawayFilter(filters.FilterSet):
    created_by = filters.CharFilter(field_name='created_by__username')
    tag = filters.CharFilter(field_name='tags__name', lookup_expr='icontains')

    class Meta:
        model = Takeaway
        fields = ['status', 'tag', 'created_by']
