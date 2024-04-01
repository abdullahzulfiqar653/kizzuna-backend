from django.db.models import Count
from rest_framework import serializers

from api.models.takeaway import Takeaway
from api.serializers.chart.base import QuerySerializer

# Filters
filter_key_mapping = {
    "created_by": "created_by__username__in",
    "tag": "tags__name__in",
    "report_id": "note__in",
    "priority": "priority__in",
    "type": "type__name__in",
    "report_type": "note__type__in",
    "created_at_before": "created_at__lt",
    "created_at_after": "created_at__gt",
}


class ChartTakeawayFilterSerializer(serializers.Serializer):
    created_by = serializers.ListSerializer(
        child=serializers.EmailField(), required=False
    )
    tag = serializers.ListSerializer(child=serializers.CharField(), required=False)
    report_id = serializers.ListSerializer(
        child=serializers.CharField(), required=False
    )
    priority = serializers.ListSerializer(
        child=serializers.ChoiceField(choices=Takeaway.Priority.choices), required=False
    )
    type = serializers.ListSerializer(child=serializers.CharField(), required=False)
    report_type = serializers.ListSerializer(
        child=serializers.CharField(), required=False
    )


# Group by
group_by_field_mapping = {
    "type_name": "type__name",
    "tag": "tags__name",
    "created_by_username": "created_by__username",
    "created_by_first_name": "created_by__first_name",
    "created_by_last_name": "created_by__last_name",
    "priority": "priority",
    "report": "note",
    "report_keyword": "note__keywords__name",
    "report_title": "note__title",
    "report_type": "note__type",
    "report_sentiment": "note__sentiment",
    "created_at": "created_at",
}
group_by_time_fields = {"created_at"}


class ChartTakeawayGroupBySerializer(serializers.Serializer):
    field = serializers.ChoiceField(choices=list(group_by_field_mapping.keys()))
    trunc = serializers.ChoiceField(
        choices=["year", "quarter", "month", "week", "day", "hour", "minute", "second"],
        default="month",
        help_text="Only applicable for datetime field.",
    )


# Aggregate
aggregate_field_mapping = {
    "takeaway": "id",
    "report": "note__id",
}
aggregate_function_mapping = {
    "count": Count,
}


class ChartTakeawayAggregateSerializer(serializers.Serializer):
    field = serializers.ChoiceField(choices=list(aggregate_field_mapping.keys()))
    function = serializers.ChoiceField(choices=list(aggregate_function_mapping.keys()))
    distinct = serializers.BooleanField(default=True)


class ChartTakeawaySerializer(serializers.Serializer, QuerySerializer):
    filter = ChartTakeawayFilterSerializer()
    group_by = ChartTakeawayGroupBySerializer(many=True)
    aggregate = ChartTakeawayAggregateSerializer()
    limit = serializers.IntegerField(default=10, max_value=100)
    offset = serializers.IntegerField(default=0)

    filter_key_mapping = filter_key_mapping
    group_by_field_mapping = group_by_field_mapping
    aggregate_field_mapping = aggregate_field_mapping
    aggregate_function_mapping = aggregate_function_mapping
    group_by_time_fields = group_by_time_fields
