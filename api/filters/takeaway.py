from django_filters import rest_framework as filters

from api.models.note import Note
from api.models.project import Project
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.user import User


def users_in_scope(request):
    "Return the list of users in project or insight"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return Project.objects.get(id=project_id).users.all()

    report_id = kwargs.get("report_id")
    if report_id is not None:
        return User.objects.filter(projects__notes__id=report_id)

    insight_id = kwargs.get("insight_id")
    if insight_id is not None:
        return User.objects.filter(created_takeaways__insights=insight_id)

    return User.objects.none()


def tags_in_scope(request):
    "Return the list of tags in project or insight"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return Tag.objects.filter(takeaways__note__project_id=project_id)

    report_id = kwargs.get("report_id")
    if report_id is not None:
        return Tag.objects.filter(takeaways__note_id=report_id)

    insight_id = kwargs.get("insight_id")
    if insight_id is not None:
        return Tag.objects.filter(takeaways__insights=insight_id)

    return Tag.objects.none()


def notes_in_scope(request):
    "Return the list of notes in project"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return Note.objects.filter(project_id=project_id)

    return Note.objects.none()


class TakeawayFilter(filters.FilterSet):
    created_by = filters.ModelMultipleChoiceFilter(
        field_name="created_by__username",
        to_field_name="username",
        queryset=users_in_scope,
    )
    tag = filters.ModelMultipleChoiceFilter(
        field_name="tags__name", to_field_name="name", queryset=tags_in_scope
    )
    report_id = filters.ModelMultipleChoiceFilter(
        field_name="note", to_field_name="id", queryset=notes_in_scope
    )
    priority = filters.MultipleChoiceFilter(choices=Takeaway.Priority.choices)

    class Meta:
        model = Takeaway
        fields = ["priority", "tag", "created_by"]
