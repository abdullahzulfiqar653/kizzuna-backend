from django_filters import rest_framework as filters

from project.models import Project
from tag.models import Tag
from takeaway.models import Takeaway


def auth_users_in_project(request):
    project_id = request.parser_context['kwargs']['project_id']
    return Project.objects.get(id=project_id).users.all()


def takeaway_tags_in_project(request):
    project_id = request.parser_context['kwargs']['project_id']
    return Tag.objects.filter(takeaway__note__project_id=project_id)


def takeaways_in_project(request):
    project_id = request.parser_context['kwargs']['project_id']
    return Takeaway.objects.filter(note__project_id=project_id)


class TakeawayFilter(filters.FilterSet):
    created_by = filters.ModelMultipleChoiceFilter(field_name='created_by__username', to_field_name='username', queryset=auth_users_in_project)
    tag = filters.ModelMultipleChoiceFilter(field_name='tags__name', to_field_name='name', queryset=takeaway_tags_in_project)
    status = filters.ModelMultipleChoiceFilter(field_name='status', to_field_name='status', queryset=takeaways_in_project)

    class Meta:
        model = Takeaway
        fields = ['status', 'tag', 'created_by']
