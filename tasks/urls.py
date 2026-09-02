from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('kanban/', views.kanban_view, name='kanban'),
    path('<int:pk>/update-status/', views.update_task_status, name='update_task_status'),
]