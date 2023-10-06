# api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from note.views import (NoteListCreateView, NoteRetrieveUpdateDeleteView,
                        NoteTagDestroyView, NoteTagListCreateView,
                        NoteTakeawayListCreateView,
                        NoteTakeawayTagGenerateView)
from project.views import (ProjectAuthUserListView, ProjectListCreateView,
                           ProjectNoteListCreateView,
                           ProjectRetrieveUpdateDeleteView,
                           ProjectTakeawayListView)
from tag.views import TagListCreateView, TagRetrieveUpdateDeleteView
from takeaway.views import (TakeawayListCreateView,
                            TakeawayRetrieveUpdateDeleteView,
                            TakeawayTagCreateView, TakeawayTagDestroyView)
from user.views import (AuthUserProjectListView, AuthUserRetrieveUpdateView,
                        AuthUserWorkspaceListView, UserListCreateView,
                        UserRetrieveUpdateDeleteView)
from workspace.views import (WorkspaceListCreateView,
                             WorkspaceProjectListCreateView,
                             WorkspaceUserListView)

from .views import (DoPasswordResetView, InvitationSignupCreateView,
                    InvitationStatusRetrieveView, InviteUserView,
                    PasswordUpdateView, RequestPasswordResetView, SignupView,
                    TokenObtainPairAndRefreshView, api_root)

urlpatterns = [
    path('', api_root, name='api-root'),

    path('token/', TokenObtainPairAndRefreshView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # path('reports/', NoteListCreateView.as_view(), name='note-list-create'),
    path('reports/<str:pk>/', NoteRetrieveUpdateDeleteView.as_view(), name='note-retrieve-update-delete'),
    path('reports/<str:report_id>/takeaways/', NoteTakeawayListCreateView.as_view(), name='note-takeaway-list-create'),
    path('reports/<str:report_id>/tags/', NoteTagListCreateView.as_view(), name='note-tag-list-create'),
    path('reports/<str:report_id>/tags/<str:tag_id>/', NoteTagDestroyView.as_view(), name='note-tag-destroy'),
    path('reports/<str:report_id>/generate-tags/', NoteTakeawayTagGenerateView.as_view(), name='note-takeaway-tag-generate'),

    path('projects/', ProjectListCreateView.as_view(), name='project-list-create'),
    path('projects/<str:pk>/', ProjectRetrieveUpdateDeleteView.as_view(), name='project-retrieve-update-delete'),
    path('projects/<str:project_id>/users/', ProjectAuthUserListView.as_view(), name='project-user-list'),
    path('projects/<str:project_id>/reports/', ProjectNoteListCreateView.as_view(), name='project-note-list-create'),
    path('projects/<str:project_id>/takeaways/', ProjectTakeawayListView.as_view(), name='project-takeaway-list'),

    path('workspaces/', WorkspaceListCreateView.as_view(), name='workspace-list-create'),
    path('workspaces/<str:pk>/projects/', WorkspaceProjectListCreateView.as_view(), name='workspace-project-list-create'),
    path('workspaces/<str:pk>/users/', WorkspaceUserListView.as_view(), name='workspace-user-list'),

    # path('tags/', TagListCreateView.as_view(), name='tag-list-create'),
    # path('tags/<str:pk>/', TagRetrieveUpdateDeleteView.as_view(), name='tag-retrieve-update-delete'),

    # path('takeaways/', TakeawayListCreateView.as_view(), name='takeaway-list-create'),
    path('takeaways/<str:pk>/', TakeawayRetrieveUpdateDeleteView.as_view(), name='takeaway-retrieve-update-delete'),
    path('takeaways/<str:takeaway_id>/tags/', TakeawayTagCreateView.as_view(), name='takeaway-tag-create'),
    path('takeaways/<str:takeaway_id>/tags/<str:tag_id>/', TakeawayTagDestroyView.as_view(), name='takeaway-tag-destroy'),

    path('signup/', SignupView.as_view(), name='signup-create'),
    path('invitation/signup/', InvitationSignupCreateView.as_view(), name='invited-signup-create'),
    path('invitation/status/', InvitationStatusRetrieveView.as_view(), name='invitation-status-retrieve'),
    
    # path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/invite/', InviteUserView.as_view(), name='user-invite'),
    # path('users/<int:pk>/', UserRetrieveUpdateDeleteView.as_view(), name='user-retrieve-update-delete'),
    path('auth-users/', AuthUserRetrieveUpdateView.as_view(), name='auth-user-retrieve-update'),

    # path('users/<int:auth_user_id>/workspaces/', AuthUserWorkspaceListView.as_view(), name='user-workspace-list'),
    # path('users/<int:auth_user_id>/projects/', AuthUserProjectListView.as_view(), name='user-project-list'),
    
    path('password/update/', PasswordUpdateView.as_view(), name='password-update'),
    path('password/request-reset/', RequestPasswordResetView.as_view(), name='password-request-reset'),
    path('password/do-reset/', DoPasswordResetView.as_view(), name='password-do-reset'),
]