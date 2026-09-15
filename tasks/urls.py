from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list_view, name='task_list'),
    path('<int:project_pk>/kanban/', views.kanban_view, name='kanban'),
    path('<int:project_pk>/backlog/', views.backlog_view, name='backlog'),
    path('<int:project_pk>/update-status/<int:pk>/', views.update_task_status, name='update_task_status'),
]