from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list_view, name='task_list'),
    path('<int:project_pk>/kanban/', views.kanban_view, name='kanban'),
    path('<int:project_pk>/backlog/', views.backlog_view, name='backlog'),
    path('<int:project_pk>/nouvelle/', views.task_create, name='task_create'),
    path('<int:project_pk>/<int:pk>/modifier/', views.task_edit, name='task_edit'),
    path('<int:project_pk>/<int:pk>/supprimer/', views.task_delete, name='task_delete'),
    path('<int:project_pk>/update-status/<int:pk>/', views.update_task_status, name='update_task_status'),
]
