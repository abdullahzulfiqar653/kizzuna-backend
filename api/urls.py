# api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from user.views import (
    UserListCreateView, 
    UserRetrieveUpdateDeleteView,
    AuthUserWorkspaceListView,
    AuthUserProjectListView
    )
from workspace.views import (
    WorkspaceUserListView,
    WorkspaceListCreateView, 
    WorkspaceRetrieveUpdateDeleteView
)
from project.views import (
    ProjectUserListView,
    ProjectNoteListCreateView,
    ProjectTakeawayListView,
)
from note.views import (
    NoteTakeawayListCreateView,
)
from takeaway.views import (
    TakeawayTagCreateView,
    TakeawayTagDestroyView,
)
from .views import (api_root,
    SignupView, 
    DoPasswordResetView,
    NoteListCreateView, 
    NoteRetrieveUpdateDeleteView,
    PasswordUpdateView, 
    ProjectListCreateView, 
    ProjectRetrieveUpdateDeleteView, 
    RequestPasswordResetView,
    TagListCreateView, 
    TagRetrieveUpdateDeleteView, 
    TakeawayListCreateView, 
    TakeawayRetrieveUpdateDeleteView, 
    TokenObtainPairAndRefreshView
)

urlpatterns = [
    path('', api_root, name='api-root'),

    path('token/', TokenObtainPairAndRefreshView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('reports/', NoteListCreateView.as_view(), name='note-list-create'),
    path('reports/<str:pk>/', NoteRetrieveUpdateDeleteView.as_view(), name='note-retrieve-update-delete'),
    path('reports/<str:report_id>/takeaways/', NoteTakeawayListCreateView.as_view(), name='note-takeaway-list-create'),

    path('projects/', ProjectListCreateView.as_view(), name='project-list-create'),
    path('projects/<str:pk>/', ProjectRetrieveUpdateDeleteView.as_view(), name='project-retrieve-update-delete'),
    path('projects/<str:project_id>/users/', ProjectUserListView.as_view(), name='project-user-list'),
    path('projects/<str:project_id>/reports/', ProjectNoteListCreateView.as_view(), name='project-note-list-create'),
    path('projects/<str:project_id>/takeaways/', ProjectTakeawayListView.as_view(), name='project-takeaway-list'),

    path('workspaces/', WorkspaceListCreateView.as_view(), name='workspace-list-create'),
    path('workspaces/<str:pk>/', WorkspaceRetrieveUpdateDeleteView.as_view(), name='workspace-retrieve-update-delete'),
    path('workspaces/<str:pk>/users/', WorkspaceUserListView.as_view(), name='workspace-user-list'),

    path('tags/', TagListCreateView.as_view(), name='tag-list-create'),
    path('tags/<str:pk>/', TagRetrieveUpdateDeleteView.as_view(), name='tag-retrieve-update-delete'),

    path('takeaways/', TakeawayListCreateView.as_view(), name='takeaway-list-create'),
    path('takeaways/<str:pk>/', TakeawayRetrieveUpdateDeleteView.as_view(), name='takeaway-retrieve-update-delete'),
    path('takeaways/<str:takeaway_id>/tags/', TakeawayTagCreateView.as_view(), name='takeaway-tag-create'),
    path('takeaways/<str:takeaway_id>/tags/<str:tag_id>/', TakeawayTagDestroyView.as_view(), name='takeaway-tag-destroy'),

    path('signup/', SignupView.as_view(), name='signup-create'),
    
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserRetrieveUpdateDeleteView.as_view(), name='user-retrieve-update-delete'),

    path('users/<int:auth_user_id>/workspaces/', AuthUserWorkspaceListView.as_view(), name='user-workspace-list'),
    path('users/<int:auth_user_id>/projects/', AuthUserProjectListView.as_view(), name='user-project-list'),
    
    path('password/update/', PasswordUpdateView.as_view(), name='password-update'),
    path('password/request-reset/', RequestPasswordResetView.as_view(), name='password-request-reset'),
    path('password/do-reset/', DoPasswordResetView.as_view(), name='password-do-reset'),
]