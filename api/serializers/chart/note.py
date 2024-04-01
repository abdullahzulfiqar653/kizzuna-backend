from django.db.models import Count
from rest_framework import serializers

from api.serializers.chart.base import QuerySerializer

# Filters
filter_key_mapping = {
    "organization": "organizations__name__in",
    "type": "type__in",
    "revenue": "revenue__in",
    "sentiment": "sentiment__in",
    "author": "author__username__in",
    "keyword": "keywords__name__in",
    "created_at_before": "created_at__lt",
    "created_at_after": "created_at__gt",
}


class ChartNoteFilterSerializer(serializers.Serializer):
    organization = serializers.ListSerializer(
        child=serializers.CharField(), required=False
    )
    type = serializers.ListSerializer(child=serializers.CharField(), required=False)
    revenue = serializers.ListSerializer(child=serializers.CharField(), required=False)
    sentiment = serializers.ListSerializer(
        child=serializers.CharField(), required=False
    )
    author = serializers.ListSerializer(child=serializers.CharField(), required=False)
    keyword = serializers.ListSerializer(child=serializers.CharField(), required=False)
    created_at_before = serializers.DateTimeField(required=False)
    created_at_after = serializers.DateTimeField(required=False)


# Group by
group_by_field_mapping = {
    "organization": "organizations__name",
    "type": "type",
    "revenue": "revenue",
    "sentiment": "sentiment",
    "author_username": "author__username",
    "author_first_name": "author__first_name",
    "author_last_name": "author__last_name",
    "keyword": "keywords__name",
    "created_at": "created_at",
}
group_by_time_fields = {"created_at"}


class ChartNoteGroupBySerializer(serializers.Serializer):
    field = serializers.ChoiceField(choices=list(group_by_field_mapping.keys()))
    trunc = serializers.ChoiceField(
        choices=["year", "quarter", "month", "week", "day", "hour", "minute", "second"],
        default="month",
        help_text="Only applicable for datetime field.",
    )


# Aggregate
aggregate_field_mapping = {"report": "id"}
aggregate_function_mapping = {"count": Count}


class ChartNoteAggregateSerializer(serializers.Serializer):
    field = serializers.ChoiceField(choices=list(aggregate_field_mapping.keys()))
    function = serializers.ChoiceField(choices=list(aggregate_function_mapping.keys()))
    distinct = serializers.BooleanField(default=True)


class ChartNoteSerializer(serializers.Serializer, QuerySerializer):
    filter = ChartNoteFilterSerializer()
    group_by = ChartNoteGroupBySerializer(many=True)
    aggregate = ChartNoteAggregateSerializer()
    limit = serializers.IntegerField(default=10, max_value=100)
    offset = serializers.IntegerField(default=0)

    filter_key_mapping = filter_key_mapping
    group_by_field_mapping = group_by_field_mapping
    aggregate_field_mapping = aggregate_field_mapping
    aggregate_function_mapping = aggregate_function_mapping
    group_by_time_fields = group_by_time_fields
