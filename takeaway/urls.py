from django.urls import path
from . import views

urlpatterns = [
    path('', views.takeaway_list, name='takeaway-list'),
    path('create', views.takeaway_create, name='takeaway-create'),
    path('<str:takeaway_id>/detail/', views.takeaway_detail, name='takeaway-detail'),
    path('<str:takeaway_id>/update/', views.takeaway_update, name='takeaway-update'),
    path('<str:takeaway_id>/delete/', views.takeaway_delete, name='takeaway-delete'),
]