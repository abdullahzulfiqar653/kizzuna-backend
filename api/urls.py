# api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from note.views import (NoteHighlightCreateView, NoteKeywordDestroyView,
                        NoteKeywordListCreateView,
                        NoteRetrieveUpdateDeleteView, NoteTagGenerateView,
                        NoteTakeawayListCreateView)
from project.views import (ProjectAuthUserListView, ProjectCompanyListView,
                           ProjectNoteListCreateView,
                           ProjectRetrieveUpdateDeleteView, ProjectTagListView,
                           ProjectTakeawayListView)
from project.views.project_insight import ProjectInsightListCreateView
from takeaway.views import (InsightRetrieveUpdateDeleteView,
                            InsightTakeawayListCreateView,
                            TakeawayRetrieveUpdateDeleteView,
                            TakeawayTagCreateView, TakeawayTagDestroyView)
from takeaway.views.insight_takeaway import InsightTakeawayDeleteView
from user.views import AuthUserRetrieveUpdateView
from workspace.views import (WorkspaceListCreateView,
                             WorkspaceProjectListCreateView,
                             WorkspaceUserListView)

from .views import (DoPasswordResetView, InvitationSignupCreateView,
                    InvitationStatusRetrieveView, InviteUserView,
                    PasswordUpdateView, RequestPasswordResetView, SignupView,
                    TokenObtainPairAndRefreshView)

urlpatterns = [
    path('token/', TokenObtainPairAndRefreshView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('reports/<str:pk>/', NoteRetrieveUpdateDeleteView.as_view(), name='note-retrieve-update-delete'),
    path('reports/<str:report_id>/takeaways/', NoteTakeawayListCreateView.as_view(), name='note-takeaway-list-create'),
    path('reports/<str:report_id>/highlights/', NoteHighlightCreateView.as_view(), name='note-highlight-create'),
    path('reports/<str:report_id>/keywords/', NoteKeywordListCreateView.as_view(), name='note-keyword-list-create'),
    path('reports/<str:report_id>/keywords/<str:keyword_id>/', NoteKeywordDestroyView.as_view(), name='note-keyword-destroy'),
    path('reports/<str:report_id>/tags/generate/', NoteTagGenerateView.as_view(), name='note-tag-generate'),

    path('projects/<str:pk>/', ProjectRetrieveUpdateDeleteView.as_view(), name='project-retrieve-update-delete'),
    path('projects/<str:project_id>/users/', ProjectAuthUserListView.as_view(), name='project-user-list'),
    path('projects/<str:project_id>/reports/', ProjectNoteListCreateView.as_view(), name='project-note-list-create'),
    path('projects/<str:project_id>/takeaways/', ProjectTakeawayListView.as_view(), name='project-takeaway-list'),
    path('projects/<str:project_id>/tags/', ProjectTagListView.as_view(), name='project-tag-list'),
    path('projects/<str:project_id>/companies/', ProjectCompanyListView.as_view(), name='project-company-list'),
    path('projects/<str:project_id>/insights/', ProjectInsightListCreateView.as_view(), name='project-insight-list-create'),

    path('workspaces/', WorkspaceListCreateView.as_view(), name='workspace-list-create'),
    path('workspaces/<str:workspace_id>/projects/', WorkspaceProjectListCreateView.as_view(), name='workspace-project-list-create'),
    path('workspaces/<str:pk>/users/', WorkspaceUserListView.as_view(), name='workspace-user-list'),

    path('takeaways/<str:pk>/', TakeawayRetrieveUpdateDeleteView.as_view(), name='takeaway-retrieve-update-delete'),
    path('takeaways/<str:takeaway_id>/tags/', TakeawayTagCreateView.as_view(), name='takeaway-tag-create'),
    path('takeaways/<str:takeaway_id>/tags/<str:tag_id>/', TakeawayTagDestroyView.as_view(), name='takeaway-tag-destroy'),

    path('insights/<str:pk>/', InsightRetrieveUpdateDeleteView.as_view(), name='insight-retrieve-update-delete'),
    path('insights/<str:insight_id>/takeaways/', InsightTakeawayListCreateView.as_view(), name='insight-takeaway-list-create'),
    path('insights/<str:insight_id>/takeaways/delete/', InsightTakeawayDeleteView.as_view(), name='insight-takeaway-delete'),

    path('signup/', SignupView.as_view(), name='signup-create'),
    path('invitation/signup/', InvitationSignupCreateView.as_view(), name='invited-signup-create'),
    path('invitation/status/', InvitationStatusRetrieveView.as_view(), name='invitation-status-retrieve'),

    path('users/invite/', InviteUserView.as_view(), name='user-invite'),
    path('auth-users/', AuthUserRetrieveUpdateView.as_view(), name='auth-user-retrieve-update'),

    path('password/update/', PasswordUpdateView.as_view(), name='password-update'),
    path('password/request-reset/', RequestPasswordResetView.as_view(), name='password-request-reset'),
    path('password/do-reset/', DoPasswordResetView.as_view(), name='password-do-reset'),
]
