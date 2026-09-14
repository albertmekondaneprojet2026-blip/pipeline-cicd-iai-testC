from django.urls import path
from . import views

app_name = 'workspaces'

urlpatterns = [
    path('equipe/', views.team_view, name='team'),
    path('parametres/', views.settings_view, name='settings'),
]
