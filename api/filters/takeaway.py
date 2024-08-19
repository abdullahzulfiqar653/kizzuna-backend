from django_filters import rest_framework as filters

from api.filters.patch import ModelMultipleChoiceFilter
from api.models.note import Note
from api.models.note_type import NoteType
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType
from api.models.user import User


def users_in_scope(request):
    "Return the list of users in project or insight"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return User.objects.filter(
            created_takeaways__note__project=project_id
        ).distinct()

    report_id = kwargs.get("report_id")
    if report_id is not None:
        return User.objects.filter(created_takeaways__note=report_id).distinct()

    insight_id = kwargs.get("insight_id")
    if insight_id is not None:
        return User.objects.filter(created_takeaways__insights=insight_id).distinct()

    asset_id = kwargs.get("asset_id")
    if asset_id is not None:
        return User.objects.filter(created_takeaways__note__assets=asset_id).distinct()

    block_id = kwargs.get("block_id")
    if block_id is not None:
        return User.objects.filter(
            created_takeaways__note__assets__blocks=block_id
        ).distinct()

    playbook_id = kwargs.get("playbook_id")
    if playbook_id is not None:
        return User.objects.filter(
            created_takeaways__note__project__playbooks=playbook_id
        ).distinct()

    return User.objects.none()


def tags_in_scope(request):
    "Return the list of tags in project or insight"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return Tag.objects.filter(takeaways__note__project=project_id)

    report_id = kwargs.get("report_id")
    if report_id is not None:
        return Tag.objects.filter(takeaways__note=report_id)

    insight_id = kwargs.get("insight_id")
    if insight_id is not None:
        return Tag.objects.filter(takeaways__insights=insight_id)

    asset_id = kwargs.get("asset_id")
    if asset_id is not None:
        return Tag.objects.filter(takeaways__note__project__assets=asset_id)

    block_id = kwargs.get("block_id")
    if block_id is not None:
        return Tag.objects.filter(takeaways__note__project__assets__blocks=block_id)

    playbook_id = kwargs.get("playbook_id")
    if playbook_id is not None:
        return Tag.objects.filter(takeaways__note__project__playbooks=playbook_id)

    return Tag.objects.none()


def notes_in_scope(request):
    "Return the list of notes in project"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return Note.objects.filter(project_id=project_id)

    insight_id = kwargs.get("insight_id")
    if insight_id is not None:
        return Note.objects.filter(takeaways__insights=insight_id)

    asset_id = kwargs.get("asset_id")
    if asset_id is not None:
        return Note.objects.filter(project__assets=asset_id)

    block_id = kwargs.get("block_id")
    if block_id is not None:
        return Note.objects.filter(project__assets__blocks=block_id)

    playbook_id = kwargs.get("playbook_id")
    if playbook_id is not None:
        return Note.objects.filter(playbooks__id=playbook_id)

    return Note.objects.none()


def note_types_in_scope(request):
    notes = notes_in_scope(request)
    return NoteType.objects.filter(notes__in=notes)


def takeaway_types_in_scope(request):
    "Return the list of takeaway types in project"
    kwargs = request.parser_context["kwargs"]

    project_id = kwargs.get("project_id")
    if project_id is not None:
        return TakeawayType.objects.filter(takeaways__note__project_id=project_id)

    report_id = kwargs.get("report_id")
    if report_id is not None:
        return TakeawayType.objects.filter(takeaways__note=report_id)

    insight_id = kwargs.get("insight_id")
    if insight_id is not None:
        return TakeawayType.objects.filter(takeaways__insights=insight_id)

    asset_id = kwargs.get("asset_id")
    if asset_id is not None:
        return TakeawayType.objects.filter(takeaways__note__project__assets=asset_id)

    block_id = kwargs.get("block_id")
    if block_id is not None:
        return TakeawayType.objects.filter(
            takeaways__note__project__assets__blocks=block_id
        )

    playbook_id = kwargs.get("playbook_id")
    if playbook_id is not None:
        return TakeawayType.objects.filter(
            takeaways__note__project__playbooks=playbook_id
        )

    return TakeawayType.objects.none()


class TakeawayFilter(filters.FilterSet):
    is_created_by_bot = filters.BooleanFilter(
        field_name="created_by", method="filter_is_created_by_bot"
    )
    created_by = ModelMultipleChoiceFilter(
        field_name="created_by__username",
        to_field_name="username",
        queryset=users_in_scope,
    )
    tag = ModelMultipleChoiceFilter(
        field_name="tags__name", to_field_name="name", queryset=tags_in_scope
    )
    report_id = ModelMultipleChoiceFilter(
        field_name="note", to_field_name="id", queryset=notes_in_scope
    )
    priority = filters.MultipleChoiceFilter(choices=Takeaway.Priority.choices)
    type = ModelMultipleChoiceFilter(
        field_name="type__name", to_field_name="name", queryset=takeaway_types_in_scope
    )
    report_type = ModelMultipleChoiceFilter(
        field_name="note__type__name",
        to_field_name="name",
        queryset=note_types_in_scope,
    )
    created_at = filters.DateFromToRangeFilter(field_name="created_at")

    class Meta:
        model = Takeaway
        fields = [
            "priority",
            "tag",
            "created_by",
            "is_created_by_bot",
            "created_at",
            "type",
            "report_type",
            "report_id",
        ]

    def filter_is_created_by_bot(self, queryset, name, value):
        match value:
            case True:
                return queryset.filter(created_by__username="bot@raijin.ai")
            case False:
                return queryset.exclude(created_by__username="bot@raijin.ai")
            case _:
                return queryset


class NoteTakeawayFilter(TakeawayFilter):
    report_id = None
    report_type = None

    class Meta:
        model = Takeaway
        fields = ["priority", "tag", "created_by", "created_at", "type"]
