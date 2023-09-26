from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_list, name='user-list'),
    path('<int:user_id>/', views.user_detail, name='user-detail'),
    path('create/', views.user_create, name='user-create'),
    path('<int:user_id>/update/', views.user_update, name='user-update'),
    path('<int:user_id>/delete/', views.user_delete, name='user-delete'),
]