from django.urls import path
from . import views

urlpatterns = [
    path('<str:note_id>/attachment/<str:attachment_id>/transcribe', views.transcribe_create, name='transcribe-create'),
]
