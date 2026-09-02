from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Task
from projects.models import Project


@login_required
def kanban_view(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk)
    tasks = Task.objects.filter(project=project)
    context = {
        'project': project,
        'todo_tasks': tasks.filter(status='todo'),
        'in_progress_tasks': tasks.filter(status='in_progress'),
        'done_tasks': tasks.filter(status='done'),
    }
    return render(request, 'tasks/kanban.html', context)


@require_POST
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    new_status = request.POST.get('status')
    if new_status in dict(Task.Status.choices):
        task.status = new_status
        task.save()
        return JsonResponse({'success': True, 'status': task.status})
    return JsonResponse({'success': False}, status=400)