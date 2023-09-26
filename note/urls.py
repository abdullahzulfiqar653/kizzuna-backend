from django.urls import path
from . import views

urlpatterns = [
    path('', views.note_list, name='note-list'),
    path('create/', views.note_create, name='note-create'),
    path('<str:note_id>/', views.note_detail, name='note-detail'),

    path('<str:note_id>/update/', views.note_update, name='note-update'),
    path('<str:note_id>/delete/', views.note_delete, name='note-delete'),
    path('<str:note_id>/summarize/', views.note_create_summary, name='note-create-summary'),
    
    path('<str:note_id>/attachment', views.attachment_list, name='attachment-list'),
    path('<str:note_id>/attachment/create', views.attachment_create, name='attachment-create'),
    path('<str:note_id>/attachment/<str:attachment_id>', views.attachment_detail, name='attachment-detail'),
]