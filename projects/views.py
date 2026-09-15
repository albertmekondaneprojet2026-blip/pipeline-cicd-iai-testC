from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import Http404

from .models import Project, Sprint, Milestone, Goal
from tasks.models import Task
from workspaces.models import TeamMember
from workspaces.utils import get_user_workspace

STATUS_LABELS = {
    Project.Status.PLANNED: ('Planifie', 'badge-blue'),
    Project.Status.IN_PROGRESS: ('En cours', 'badge-green'),
    Project.Status.IN_REVIEW: ('En revision', 'badge-purple'),
    Project.Status.DONE: ('Termine', 'badge-gray'),
}


def get_user_project_or_404(user, pk):
    """Renvoie le projet pk UNIQUEMENT s'il appartient a l'espace de travail
    de l'utilisateur connecte. Sinon, leve un 404 (et non un 403) pour ne
    pas confirmer a un attaquant que le projet existe (evite l'enumeration
    d'ID / IDOR)."""
    workspace = get_user_workspace(user)
    if not workspace:
        raise Http404("Projet introuvable.")
    return get_object_or_404(Project, pk=pk, workspace=workspace)


@login_required
def project_list(request):
    workspace = get_user_workspace(request.user)
    projects = Project.objects.filter(workspace=workspace).select_related('workspace') if workspace else Project.objects.none()

    for project in projects:
        tasks = Task.objects.filter(project=project)
        total = tasks.count()
        done = tasks.filter(status=Task.Status.DONE).count()
        project.progress_percent = round((done / total) * 100) if total else 0
        project.member_count = TeamMember.objects.filter(workspace=project.workspace).count()
        project.status_label, project.status_css = STATUS_LABELS.get(project.status, ('En cours', 'badge-green'))

    return render(request, 'projects/project_list.html', {'projects': projects})


@login_required
def project_dashboard(request, pk):
    project = get_user_project_or_404(request.user, pk)
    tasks = Task.objects.filter(project=project)

    stats = tasks.aggregate(
        total=Count('id'),
        todo=Count('id', filter=Q(status=Task.Status.TODO)),
        in_progress=Count('id', filter=Q(status=Task.Status.IN_PROGRESS)),
        done=Count('id', filter=Q(status=Task.Status.DONE)),
    )
    progress_percent = round((stats['done'] / stats['total']) * 100) if stats['total'] else 0

    context = {
        'project': project,
        'stats': stats,
        'progress_percent': progress_percent,
        'active_sprint': Sprint.objects.filter(project=project, is_active=True).first(),
        'recent_tasks': tasks.order_by('-updated_at')[:5],
    }
    return render(request, 'projects/project_dashboard.html', context)


@login_required
def reports_view(request):
    workspace = get_user_workspace(request.user)
    projects = Project.objects.filter(workspace=workspace) if workspace else Project.objects.none()
    tasks = Task.objects.filter(project__workspace=workspace) if workspace else Task.objects.none()
    members = TeamMember.objects.filter(workspace=workspace) if workspace else TeamMember.objects.none()
    goals = Goal.objects.filter(workspace=workspace) if workspace else Goal.objects.none()

    active_projects = projects.exclude(status=Project.Status.DONE).count()
    completed_tasks = tasks.filter(status=Task.Status.DONE).count()

    six_months_ago = date.today() - timedelta(days=180)
    monthly = (
        tasks.filter(created_at__date__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Count('id'), completed=Count('id', filter=Q(status=Task.Status.DONE)))
        .order_by('month')
    )
    chart_labels = [row['month'].strftime('%b') for row in monthly] or ['-']
    chart_totals = [row['total'] for row in monthly] or [0]
    chart_completed = [row['completed'] for row in monthly] or [0]

    total_projects = projects.count() or 1
    done_projects = projects.filter(status=Project.Status.DONE).count()
    total_tasks = tasks.count() or 1
    total_members = members.count() or 1
    total_goals = goals.count() or 1
    done_goals = goals.filter(is_completed=True).count()

    context = {
        'active_projects': active_projects,
        'completed_tasks': completed_tasks,
        'member_count': members.count(),
        'chart_labels': chart_labels,
        'chart_totals': chart_totals,
        'chart_completed': chart_completed,
        'progress_projects': {'done': done_projects, 'total': projects.count(), 'pct': round(done_projects / total_projects * 100)},
        'progress_tasks': {'done': completed_tasks, 'total': tasks.count(), 'pct': round(completed_tasks / total_tasks * 100)},
        'progress_members': {'done': members.count(), 'total': members.count() or 0, 'pct': 100 if members.count() else 0},
        'progress_goals': {'done': done_goals, 'total': goals.count(), 'pct': round(done_goals / total_goals * 100)},
        'recent_tasks': tasks.select_related('project', 'assignee').order_by('due_date')[:6],
    }
    return render(request, 'projects/reports.html', context)


@login_required
def roadmap_view(request):
    workspace = get_user_workspace(request.user)
    projects = Project.objects.filter(workspace=workspace).prefetch_related('sprints') if workspace else Project.objects.none()
    milestones = Milestone.objects.filter(workspace=workspace) if workspace else Milestone.objects.none()

    all_sprints = Sprint.objects.filter(project__workspace=workspace) if workspace else Sprint.objects.none()
    if all_sprints.exists():
        range_start = min(s.start_date for s in all_sprints)
        range_end = max(s.end_date for s in all_sprints)
    else:
        range_start, range_end = date.today(), date.today() + timedelta(days=90)

    total_days = max((range_end - range_start).days, 1)

    tick_count = 6
    timeline_labels = []
    for i in range(tick_count):
        day_offset = int(total_days * i / (tick_count - 1)) if tick_count > 1 else 0
        timeline_labels.append((range_start + timedelta(days=day_offset)).strftime('%d %b'))

    palette = ['blue', 'green', 'purple', 'orange', 'teal']
    projects_data = []
    for idx, project in enumerate(projects):
        sprints_data = []
        for sprint in project.sprints.all():
            offset_pct = max(0, (sprint.start_date - range_start).days) / total_days * 100
            width_pct = max(((sprint.end_date - sprint.start_date).days / total_days) * 100, 2)
            sprints_data.append({'sprint': sprint, 'offset_pct': f"{offset_pct:.2f}", 'width_pct': f"{width_pct:.2f}"})
        projects_data.append({'project': project, 'sprints': sprints_data, 'color': palette[idx % len(palette)]})

    context = {
        'projects_data': projects_data,
        'milestones': milestones,
        'range_start': range_start,
        'range_end': range_end,
        'timeline_labels': timeline_labels,
    }
    return render(request, 'projects/roadmap.html', context)
