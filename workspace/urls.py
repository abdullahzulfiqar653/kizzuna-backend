from django.urls import path
from . import views

urlpatterns = [
    path('', views.workspace_list, name='workspace-list'),
    path('create/', views.workspace_create, name='workspace-create'),
    path('<str:workspace_id>/', views.workspace_detail, name='workspace-detail'),
    path('<str:workspace_id>/update/', views.workspace_update, name='workspace-update'),
    path('<str:workspace_id>/delete/', views.workspace_delete, name='workspace-delete'),
]