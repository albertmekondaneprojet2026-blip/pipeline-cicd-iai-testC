from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('<int:pk>/dashboard/', views.project_dashboard, name='project_dashboard'),
]