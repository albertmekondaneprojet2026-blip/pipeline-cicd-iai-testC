from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .models import Project, Sprint
from tasks.models import Task
from workspaces.models import TeamMember


@login_required
def project_list(request):
    """Ecran 'Projets' (liste)."""
    projects = Project.objects.select_related('workspace').all()
    for project in projects:
        tasks = Task.objects.filter(project=project)
        total = tasks.count()
        done = tasks.filter(status='done').count()
        project.progress_percent = round((done / total) * 100) if total else 0
        project.member_count = TeamMember.objects.filter(workspace=project.workspace).count()
    return render(request, 'projects/project_list.html', {'projects': projects})


@login_required
def project_dashboard(request, pk):
    """Ecran 'Resume' : statistiques agregees du projet."""
    project = get_object_or_404(Project, pk=pk)
    tasks = Task.objects.filter(project=project)

    stats = tasks.aggregate(
        total=Count('id'),
        todo=Count('id', filter=Q(status='todo')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        done=Count('id', filter=Q(status='done')),
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