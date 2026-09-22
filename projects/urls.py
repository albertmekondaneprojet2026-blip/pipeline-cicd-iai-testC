from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('nouveau/', views.project_create, name='project_create'),
    path('resume/', views.summary_view, name='summary'),
    path('rapports/', views.reports_view, name='reports'),
    path('roadmap/', views.roadmap_view, name='roadmap'),
    path('<int:pk>/dashboard/', views.project_dashboard, name='project_dashboard'),
    path('<int:pk>/modifier/', views.project_edit, name='project_edit'),
    path('<int:pk>/archiver/', views.project_archive, name='project_archive'),
    path('<int:pk>/supprimer/', views.project_delete, name='project_delete'),
    path('<int:project_pk>/sprints/nouveau/', views.sprint_create, name='sprint_create'),
    path('<int:project_pk>/sprints/<int:pk>/', views.sprint_detail, name='sprint_detail'),
    path('<int:project_pk>/sprints/<int:pk>/modifier/', views.sprint_edit, name='sprint_edit'),
    path('<int:project_pk>/sprints/<int:pk>/demarrer/', views.sprint_start, name='sprint_start'),
    path('<int:project_pk>/sprints/<int:pk>/cloturer/', views.sprint_close, name='sprint_close'),
    path('<int:project_pk>/sprints/<int:pk>/annuler/', views.sprint_cancel, name='sprint_cancel'),
]