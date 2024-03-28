from django.db.models import Count, F
from rest_framework import serializers

from api.models.takeaway import Takeaway

filter_key_mapping = {
    "created_by": "created_by__username",
    "tag": "tags__name",
    "report_id": "note",
    "priority": "priority",
    "type": "type__name",
    "report_type": "note__type",
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


group_by_field_mapping = {
    "type": "type__name",
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
}


class ChartTakeawayGroupBySerializer(serializers.Serializer):
    field = serializers.ChoiceField(choices=list(group_by_field_mapping.keys()))


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


class ChartTakeawaySerializer(serializers.Serializer):
    filter = ChartTakeawayFilterSerializer()
    group_by = ChartTakeawayGroupBySerializer(many=True)
    aggregate = ChartTakeawayAggregateSerializer()
    limit = serializers.IntegerField(default=10, max_value=100)
    offset = serializers.IntegerField(default=0)

    def query(self, queryset):
        data = self.data

        # Filters
        filters = {
            f"{filter_key_mapping[key]}__in": value
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


# # =================================================================
# # Example of group by tag family
# # =================================================================
# from django.db.models import Count, F
# from pyperclip import copy

# from api.models.takeaway import Takeaway

# copy(
#     str(
#         Takeaway.objects.filter(type__name="collaboration")
#         .filter(tags__project__id="project1")
#         .annotate(tag1=F("tags__name"))
#         .filter(tags__project__id="project2")
#         .annotate(tag2=F("tags__name"))
#         .values("tag1", "tag2")
#         .annotate(takeaway_count=Count("id", distinct=True))
#         .query
#     )
# )
