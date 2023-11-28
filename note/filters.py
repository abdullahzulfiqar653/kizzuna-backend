from django_filters import rest_framework as filters

from note.models import Note
from project.models import Project


def notes_in_project(request):
    project_id = request.parser_context["kwargs"]["project_id"]
    return Note.objects.filter(project_id=project_id)


def auth_users_in_project(request):
    project_id = request.parser_context["kwargs"]["project_id"]
    return Project.objects.get(id=project_id).users.all()


class NoteFilter(filters.FilterSet):
    company_name = filters.ModelMultipleChoiceFilter(
        to_field_name="company_name", queryset=notes_in_project
    )
    type = filters.ModelMultipleChoiceFilter(
        to_field_name="type", queryset=notes_in_project
    )
    revenue = filters.MultipleChoiceFilter(choices=Note.Revenue.choices)
    sentiment = filters.MultipleChoiceFilter(choices=Note.Sentiment.choices)
    author = filters.ModelMultipleChoiceFilter(
        field_name="author__username",
        to_field_name="username",
        queryset=auth_users_in_project,
    )
    created_at = filters.DateFromToRangeFilter(field_name="created_at")
