from django.db.models import DateTimeField, F
from django.db.models.functions import Trunc
from rest_framework import serializers


def get_order_by_fields(group_by_field_mapping):
    """
    Get the order_by fields.
    """
    order_by_fields = [
        (field, f"Order by {field} ascendingly")
        for field in group_by_field_mapping.keys()
    ]
    order_by_fields += [("aggregate", f"Order by aggregated field ascendingly")]
    order_by_fields += [
        (f"-{field}", f"Order by {field} descendingly") for field, _ in order_by_fields
    ]
    return order_by_fields


class QuerySerializer:
    filter_key_mapping = {}
    group_by_field_mapping = {}
    aggregate_field_mapping = {}
    aggregate_function_mapping = {}
    group_by_time_fields = {}

    def validate(self, data):
        order_by_keys = {item.lstrip("-") for item in data["order_by"]}
        group_by_keys = {item["field"] for item in data["group_by"]} | {"aggregate"}
        if order_by_keys - group_by_keys:
            raise serializers.ValidationError(
                {
                    "order_by": [
                        f"Field '{field}' not found in group_by"
                        for field in order_by_keys - group_by_keys
                    ]
                }
            )
        return data

    def query(self, queryset):
        data = self.data

        # Filters
        filters = {
            f"{self.filter_key_mapping[key]}": value
            for key, value in data["filter"].items()
            if value
        }
        queryset = queryset.filter(**filters)

        # Group by
        group_by_kwargs = dict()
        group_by_args = []
        group_by_exclude_null = {}
        order_by_mapping = {}
        for group_by in data["group_by"]:
            label = group_by["field"]
            field = self.group_by_field_mapping[label]
            if label == field and label not in self.group_by_time_fields:
                # If the label and the field are the same, we don't need to annotate
                # except if it is time field, we need to truncate it
                pass
            elif label in self.group_by_time_fields:
                # Truncate the time field and update the label
                label += "_" + group_by["trunc"]
                group_by_kwargs[label] = Trunc(
                    field, group_by["trunc"], output_field=DateTimeField()
                )
            else:
                group_by_kwargs[label] = F(field)
            group_by_args.append(label)
            order_by_mapping[group_by["field"]] = label
            if group_by["exclude_null"] is True:
                group_by_exclude_null[f"{label}__isnull"] = True

        # Annotate the queryset. Eg.:
        # queryset.annotate(
        #     tag=F('tags__name'),
        #     created_at_day=Trunc('created_at', 'day', output_field=DateTimeField()),
        # )
        queryset = queryset.annotate(**group_by_kwargs)
        # Group the queryset. Eg.: queryset.values('tag', 'created_at_day')
        queryset = queryset.values(*group_by_args)

        # Aggregate
        aggregate = data["aggregate"]
        aggregate_field = self.aggregate_field_mapping[aggregate["field"]]
        aggregate_function = self.aggregate_function_mapping[aggregate["function"]]
        distinct = aggregate["distinct"]
        aggregate_label = (
            f"{aggregate.get('field')}_"
            f"{'distinct_' if distinct else ''}"
            f"{aggregate.get('function')}"
        )
        aggregate_kwargs = {
            aggregate_label: aggregate_function(aggregate_field, distinct=distinct)
        }
        if len(data["group_by"]) == 0:
            # If no group_by, we just count the total number of takeaways
            queryset = queryset.aggregate(**aggregate_kwargs)
            return queryset
        queryset = queryset.annotate(**aggregate_kwargs)
        queryset = queryset.exclude(**group_by_exclude_null)

        # Order by
        order_by_mapping["aggregate"] = aggregate_label
        order_by = [
            (
                f"-{order_by_mapping[field.lstrip('-')]}"
                if field.startswith("-")
                else order_by_mapping[field]
            )
            for field in data["order_by"]
        ]
        queryset = queryset.order_by(*order_by)

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
