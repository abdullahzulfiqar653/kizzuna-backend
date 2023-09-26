from django.urls import path
from . import views

app_name = 'web_app'
urlpatterns = [
    path('protected/', views.protected, name='protected'),
]