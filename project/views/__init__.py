from .project import ProjectRetrieveUpdateDeleteView
from .project_authuser import ProjectAuthUserListView
from .project_company import ProjectCompanyListView
from .project_note import ProjectNoteListCreateView
from .project_tag import ProjectTagListView
from .project_takeaway import ProjectTakeawayListView
from .project_type import ProjectTypeListView

__all__ = [
    ProjectRetrieveUpdateDeleteView,
    ProjectAuthUserListView,
    ProjectCompanyListView,
    ProjectNoteListCreateView,
    ProjectTakeawayListView,
    ProjectTypeListView,
    ProjectTagListView,
]
