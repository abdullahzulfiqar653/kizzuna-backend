from django.urls import path
from . import views

urlpatterns = [
    path('', views.tag_list, name='tag-list'),
    path('<str:tag_id>/', views.tag_detail, name='tag-detail'),
    path('create/', views.tag_create, name='tag-create'),
    path('<str:tag_id>/update/', views.tag_update, name='tag-update'),
    path('<str:tag_id>/delete/', views.tag_delete, name='tag-delete'),
]