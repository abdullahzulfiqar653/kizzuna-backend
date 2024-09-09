from django_filters import rest_framework as filters

from api.models.integrations.google.calendar.event import GoogleCalendarEvent


class GoogleCalendarEventFilter(filters.FilterSet):
    start = filters.DateTimeFromToRangeFilter(field_name="start")
    end = filters.DateTimeFromToRangeFilter(field_name="end")
    meeting_url_is_null = filters.BooleanFilter(
        field_name="meeting_url", method="filter_is_null"
    )
    recall_bot_is_null = filters.BooleanFilter(
        field_name="recall_bot", method="filter_is_null"
    )

    def filter_is_null(self, queryset, name, value):
        match value:
            case True:
                return queryset.filter(**{f"{name}__isnull": True})
            case False:
                return queryset.filter(**{f"{name}__isnull": False})
            case _:
                return queryset

    class Meta:
        model = GoogleCalendarEvent
        fields = [
            "start",
            "end",
            "meeting_platform",
            "meeting_url_is_null",
            "recall_bot_is_null",
        ]
