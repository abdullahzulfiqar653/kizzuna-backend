from django_filters import rest_framework as filters
from note.models import Note
from project.models import Project

def notes_in_project(request):
    project_id = request.parser_context['kwargs']['project_id']
    return Note.objects.filter(project_id=project_id)

def auth_users_in_project(request):
    project_id = request.parser_context['kwargs']['project_id']
    return Project.objects.get(id=project_id).users.all()


class NoteFilter(filters.FilterSet):
    company_name = filters.ModelMultipleChoiceFilter(to_field_name='company_name', queryset=notes_in_project)
    revenue = filters.ModelMultipleChoiceFilter(to_field_name='revenue', queryset=notes_in_project)
    sentiment = filters.ModelMultipleChoiceFilter(to_field_name='sentiment', queryset=notes_in_project)
    author = filters.ModelMultipleChoiceFilter(field_name='author__username', to_field_name='username', queryset=auth_users_in_project)
    created_at = filters.DateFromToRangeFilter(field_name='created_at')

    class Meta:
        model = Note
        fields = ['author', 'created_at', 'company_name', 'revenue', 'sentiment']
