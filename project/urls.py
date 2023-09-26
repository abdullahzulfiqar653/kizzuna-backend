from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project-list'),
    path('create/', views.project_create, name='project-create'),
    path('<str:project_id>/', views.project_detail, name='project-detail'),
    path('<str:project_id>/update/', views.project_update, name='project-update'),
    path('<str:project_id>/delete/', views.project_delete, name='project-delete'),
]