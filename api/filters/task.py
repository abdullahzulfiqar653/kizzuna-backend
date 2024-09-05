from django_filters import rest_framework as filters

from api.models.task import Task
from api.models.user import User
from api.models.note import Note
from api.models.task_type import TaskType
from api.filters.patch import ModelMultipleChoiceFilter


def users_in_scope(request):
    """Return the list of users in project or report."""
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return User.objects.filter(created_tasks__note__project=project_id).distinct()

    report_id = kwargs.get("report_id")
    if report_id is not None:
        return User.objects.filter(created_tasks__note=report_id).distinct()

    return User.objects.none()


def notes_in_scope(request):
    """Return the list of notes in project or report."""
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return Note.objects.filter(project_id=project_id)

    report_id = kwargs.get("report_id")
    if report_id is not None:
        return Note.objects.filter(id=report_id)

    return Note.objects.none()


def task_types_in_scope(request):
    """Return the list of task types in project or notes."""
    notes = notes_in_scope(request)
    return TaskType.objects.filter(tasks__note__in=notes).distinct()


class TaskFilter(filters.FilterSet):
    is_created_by_bot = filters.BooleanFilter(
        field_name="created_by", method="filter_is_created_by_bot"
    )
    created_by = ModelMultipleChoiceFilter(
        field_name="created_by__username",
        to_field_name="username",
        queryset=users_in_scope,
    )
    assigned_to = ModelMultipleChoiceFilter(
        field_name="assigned_to__username",
        to_field_name="username",
        queryset=users_in_scope,
    )
    priority = filters.MultipleChoiceFilter(choices=Task.Priority.choices)
    status = filters.MultipleChoiceFilter(choices=Task.Status.choices)
    type = ModelMultipleChoiceFilter(
        field_name="type__name",
        to_field_name="name",
        queryset=task_types_in_scope,
    )
    due_date = filters.DateFromToRangeFilter(field_name="due_date")
    created_at = filters.DateFromToRangeFilter(field_name="created_at")

    class Meta:
        model = Task
        fields = [
            "type",
            "status",
            "priority",
            "due_date",
            "created_by",
            "created_at",
            "assigned_to",
            "is_created_by_bot",
        ]

    def filter_is_created_by_bot(self, queryset, name, value):
        match value:
            case True:
                return queryset.filter(created_by__username="bot@raijin.ai")
            case False:
                return queryset.exclude(created_by__username="bot@raijin.ai")
            case _:
                return queryset
