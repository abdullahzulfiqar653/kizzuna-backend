from django_filters import rest_framework as filters

from project.models import Project
from tag.models import Tag
from takeaway.models import Takeaway
from django.contrib.auth.models import User as AuthUser


def auth_users_in_scope(request):
    "Return the list of users in project or insight"
    kwargs = request.parser_context['kwargs']

    project_id = kwargs.get('project_id')
    if project_id is not None:
        return Project.objects.get(id=project_id).users.all()

    insight_id = kwargs.get('insight_id')
    if insight_id is not None:
        return AuthUser.objects.filter(created_takeaways__insights=insight_id)
    
    return []


def tags_in_scope(request):
    "Return the list of tags in project or insight"
    kwargs = request.parser_context['kwargs']

    project_id = kwargs.get('project_id')
    if project_id is not None:
        return Tag.objects.filter(takeaway__note__project_id=project_id)

    insight_id = kwargs.get('insight_id')
    if insight_id is not None:
        return Tag.objects.filter(takeaway__insights=insight_id)
    
    return []


class TakeawayFilter(filters.FilterSet):
    created_by = filters.ModelMultipleChoiceFilter(field_name='created_by__username', to_field_name='username', queryset=auth_users_in_scope)
    tag = filters.ModelMultipleChoiceFilter(field_name='tags__name', to_field_name='name', queryset=tags_in_scope)
    status = filters.MultipleChoiceFilter(choices=Takeaway.Status.choices)

    class Meta:
        model = Takeaway
        fields = ['status', 'tag', 'created_by']
