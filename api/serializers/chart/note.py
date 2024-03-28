from django.db.models import Count, F
from rest_framework import serializers

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


group_by_field_mapping = {
    "organization": "organizations__name",
    "type": "type",
    "revenue": "revenue",
    "sentiment": "sentiment",
    "author_username": "author_username",
    "author_first_name": "author_first_name",
    "author_last_name": "author_last_name",
    "keyword": "keywords__name",
}


class ChartNoteGroupBySerializer(serializers.Serializer):
    field = serializers.ChoiceField(choices=list(group_by_field_mapping.keys()))


aggregate_field_mapping = {"report": "id"}
aggregate_function_mapping = {"count": Count}


class ChartNoteAggregateSerializer(serializers.Serializer):
    field = serializers.ChoiceField(choices=list(aggregate_field_mapping.keys()))
    function = serializers.ChoiceField(choices=list(aggregate_function_mapping.keys()))
    distinct = serializers.BooleanField(default=True)


class ChartNoteSerializer(serializers.Serializer):
    filter = ChartNoteFilterSerializer()
    group_by = ChartNoteGroupBySerializer(many=True)
    aggregate = ChartNoteAggregateSerializer()
    limit = serializers.IntegerField(default=10, max_value=100)
    offset = serializers.IntegerField(default=0)

    def query(self, queryset):
        data = self.data

        # Filters
        filters = {
            f"{filter_key_mapping[key]}": value
            for key, value in data["filter"].items()
            if value
        }
        queryset = queryset.filter(**filters)

        # Group by
        labels = [group_by.get("field") for group_by in data["group_by"]]
        fields = [group_by_field_mapping.get(label) for label in labels]
        queryset = queryset.values(*fields)
        queryset = queryset.annotate(
            **{
                label: F(field)
                for label, field in zip(labels, fields)
                if label != field
            }
        )
        queryset = queryset.values(*labels)

        # Aggregate
        aggregate = data["aggregate"]
        aggregate_field = aggregate_field_mapping[aggregate["field"]]
        aggregate_function = aggregate_function_mapping[aggregate["function"]]
        distinct = aggregate["distinct"]
        aggregate_label = (
            f"{aggregate.get('field')}_"
            f"{'distinct_' if distinct else ''}"
            f"{aggregate.get('function')}"
        )
        queryset = queryset.annotate(
            **{aggregate_label: aggregate_function(aggregate_field, distinct=distinct)}
        )
        queryset = queryset.order_by("-" + aggregate_label)

        # Offset and limit
        start = data.get("offset")
        end = start + data.get("limit")
        queryset = queryset[start:end]
        return queryset
