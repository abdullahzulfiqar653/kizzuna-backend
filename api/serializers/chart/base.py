from django.db.models import DateTimeField
from django.db.models.functions import Trunc


class QuerySerializer:
    filter_key_mapping = {}
    group_by_field_mapping = {}
    aggregate_field_mapping = {}
    aggregate_function_mapping = {}
    group_by_time_fields = {}

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
        for group_by in data["group_by"]:
            label = group_by["field"]
            field = self.group_by_field_mapping[label]
            if label == field and label not in self.group_by_time_fields:
                # If the label and the field are the same, we don't need to annotate
                # except if it is time field, we need to truncate it
                group_by_args.append(label)
                continue
            if label in self.group_by_time_fields:
                # Truncate the time field and update the label
                label += "_" + group_by["trunc"]
                field = Trunc(field, group_by["trunc"], output_field=DateTimeField())
            group_by_kwargs[label] = field
            group_by_args.append(label)

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
