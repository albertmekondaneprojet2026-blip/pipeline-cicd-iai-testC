from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q

from .models import Task
from projects.models import Project, Sprint
from projects.views import get_user_project_or_404
from workspaces.models import TeamMember
from workspaces.utils import get_user_workspace


@login_required
def kanban_view(request, project_pk):
    project = get_user_project_or_404(request.user, project_pk)
    tasks = Task.objects.filter(project=project).select_related('assignee')

    context = {
        'project': project,
        'todo_tasks': tasks.filter(status=Task.Status.TODO),
        'in_progress_tasks': tasks.filter(status=Task.Status.IN_PROGRESS),
        'in_review_tasks': tasks.filter(status=Task.Status.IN_REVIEW),
        'done_tasks': tasks.filter(status=Task.Status.DONE),
    }
    return render(request, 'tasks/kanban.html', context)


@require_POST
@login_required
def update_task_status(request, project_pk, pk):
    project = get_user_project_or_404(request.user, project_pk)
    task = get_object_or_404(Task, pk=pk, project=project)
    new_status = request.POST.get('status')
    if new_status in dict(Task.Status.choices):
        task.status = new_status
        task.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'success': True, 'status': task.status})
    return JsonResponse({'success': False}, status=400)


@login_required
def task_list_view(request):
    workspace = get_user_workspace(request.user)
    tasks = Task.objects.filter(project__workspace=workspace).select_related('project', 'assignee') if workspace else Task.objects.none()

    query = request.GET.get('q', '').strip()
    project_filter = request.GET.get('project', '')
    priority_filter = request.GET.get('priority', '')
    status_filter = request.GET.get('status', '')
    assignee_filter = request.GET.get('assignee', '')

    if query:
        tasks = tasks.filter(title__icontains=query)
    if project_filter:
        tasks = tasks.filter(project_id=project_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if assignee_filter:
        tasks = tasks.filter(assignee_id=assignee_filter)

    projects = Project.objects.filter(workspace=workspace) if workspace else Project.objects.none()
    members = TeamMember.objects.filter(workspace=workspace).select_related('user') if workspace else TeamMember.objects.none()

    context = {
        'tasks': tasks,
        'projects': projects,
        'members': members,
        'status_choices': Task.Status.choices,
        'priority_choices': Task.Priority.choices,
        'query': query,
        'selected_project': project_filter,
        'selected_priority': priority_filter,
        'selected_status': status_filter,
        'selected_assignee': assignee_filter,
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def backlog_view(request, project_pk):
    """Ecran 'Backlog' : taches du projet groupees par sprint."""
    project = get_user_project_or_404(request.user, project_pk)
    tasks = Task.objects.filter(project=project).select_related('assignee', 'sprint')

    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    assignee_filter = request.GET.get('assignee', '')

    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(assignee__first_name__icontains=query))
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if assignee_filter:
        tasks = tasks.filter(assignee_id=assignee_filter)

    sprints = Sprint.objects.filter(project=project)
    sprint_groups = []
    for sprint in sprints:
        sprint_groups.append({'sprint': sprint, 'tasks': tasks.filter(sprint=sprint)})

    backlog_tasks = tasks.filter(sprint__isnull=True)
    if backlog_tasks.exists():
        sprint_groups.append({'sprint': None, 'tasks': backlog_tasks})

    members = TeamMember.objects.filter(workspace=project.workspace).select_related('user')

    context = {
        'project': project,
        'sprint_groups': sprint_groups,
        'members': members,
        'status_choices': Task.Status.choices,
        'priority_choices': Task.Priority.choices,
        'query': query,
    }
    return render(request, 'tasks/backlog.html', context)
