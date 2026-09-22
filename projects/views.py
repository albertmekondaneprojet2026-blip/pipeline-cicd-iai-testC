from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import Http404
from django.utils import timezone

from .models import Project, Sprint, Milestone, Goal
from .forms import ProjectForm, SprintForm
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
    projects = Project.objects.filter(workspace=workspace).select_related('workspace', 'lead') if workspace else Project.objects.none()

    show_archived = request.GET.get('archived') == '1'
    projects = projects.filter(is_archived=show_archived)

    query = request.GET.get('q', '').strip()
    if query:
        projects = projects.filter(Q(name__icontains=query) | Q(description__icontains=query))

    status_filter = request.GET.get('status', '')
    if status_filter:
        projects = projects.filter(status=status_filter)

    sort = request.GET.get('sort', '-updated_at')
    allowed_sorts = {'name', '-name', 'updated_at', '-updated_at', 'start_date', '-start_date'}
    if sort in allowed_sorts:
        projects = projects.order_by(sort)

    for project in projects:
        tasks = Task.objects.filter(project=project)
        total = tasks.count()
        done = tasks.filter(status=Task.Status.DONE).count()
        project.progress_percent = round((done / total) * 100) if total else 0
        project.member_count = TeamMember.objects.filter(workspace=project.workspace).count()
        project.status_label, project.status_css = STATUS_LABELS.get(project.status, ('En cours', 'badge-green'))

    context = {
        'projects': projects,
        'query': query,
        'status_filter': status_filter,
        'sort': sort,
        'show_archived': show_archived,
        'status_choices': Project.Status.choices,
    }
    return render(request, 'projects/project_list.html', context)


@login_required
def project_create(request):
    workspace = get_user_workspace(request.user)
    members_qs = User.objects.filter(team_memberships__workspace=workspace).distinct() if workspace else User.objects.none()

    if request.method == 'POST':
        form = ProjectForm(request.POST, members_queryset=members_qs)
        if form.is_valid():
            project = form.save(commit=False)
            project.workspace = workspace
            project.save()
            messages.success(request, f"Le projet « {project.name} » a été créé.")
            return redirect('projects:project_dashboard', pk=project.pk)
    else:
        form = ProjectForm(members_queryset=members_qs)

    return render(request, 'projects/project_form.html', {'form': form, 'is_edit': False})


@login_required
def project_edit(request, pk):
    project = get_user_project_or_404(request.user, pk)
    members_qs = User.objects.filter(team_memberships__workspace=project.workspace).distinct()

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, members_queryset=members_qs)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le projet « {project.name} » a été mis à jour.")
            return redirect('projects:project_dashboard', pk=project.pk)
    else:
        form = ProjectForm(instance=project, members_queryset=members_qs)

    return render(request, 'projects/project_form.html', {'form': form, 'is_edit': True, 'project': project})


@require_POST
@login_required
def project_archive(request, pk):
    project = get_user_project_or_404(request.user, pk)
    project.is_archived = not project.is_archived
    project.save(update_fields=['is_archived'])
    verb = 'archivé' if project.is_archived else 'désarchivé'
    messages.success(request, f"Le projet « {project.name} » a été {verb}.")
    return redirect('projects:project_list')


@require_POST
@login_required
def project_delete(request, pk):
    project = get_user_project_or_404(request.user, pk)
    name = project.name
    project.delete()
    messages.success(request, f"Le projet « {name} » a été supprimé définitivement.")
    return redirect('projects:project_list')


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
        'active_sprint': Sprint.objects.filter(project=project, status=Sprint.Status.ACTIVE).first(),
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


@login_required
def summary_view(request):
    """Ecran 'Resume' : vue d'ensemble personnelle affichee apres connexion."""
    workspace = get_user_workspace(request.user)
    projects = Project.objects.filter(workspace=workspace) if workspace else Project.objects.none()
    tasks = Task.objects.filter(project__workspace=workspace) if workspace else Task.objects.none()
    members = TeamMember.objects.filter(workspace=workspace) if workspace else TeamMember.objects.none()

    today = date.today()
    week_ago = today - timedelta(days=7)

    total_tasks = tasks.count()
    done_tasks = tasks.filter(status=Task.Status.DONE).count()
    workspace_progress = round((done_tasks / total_tasks) * 100) if total_tasks else 0

    active_projects = projects.exclude(status=Project.Status.DONE)
    todo_tasks = tasks.exclude(status=Task.Status.DONE)
    overdue_tasks = tasks.filter(due_date__lt=today).exclude(status=Task.Status.DONE)

    # --- Activite recente (deduite des donnees existantes, pas de journal dedie) ---
    activity = []
    for t in tasks.filter(status=Task.Status.DONE).select_related('assignee').order_by('-updated_at')[:4]:
        who = t.assignee.get_full_name() or t.assignee.username if t.assignee else 'quelqu\'un'
        activity.append({
            'title': f'Tâche « {t.title} »',
            'detail': f'Terminée par {who}',
            'when': t.updated_at,
            'filled': True,
        })
    for m in members.select_related('user').order_by('-joined_at')[:3]:
        activity.append({
            'title': 'Nouveau membre ajouté',
            'detail': f'{m.user.get_full_name() or m.user.username} a rejoint l\'équipe',
            'when': m.joined_at,
            'filled': False,
        })
    for p in projects.order_by('-updated_at')[:3]:
        activity.append({
            'title': f'Projet « {p.name} »',
            'detail': 'Mis à jour récemment',
            'when': p.updated_at,
            'filled': True,
        })
    activity.sort(key=lambda a: a['when'], reverse=True)
    activity = activity[:5]

    # --- Mes prochaines taches ---
    my_tasks = (
        tasks.filter(assignee=request.user)
        .exclude(status=Task.Status.DONE)
        .order_by('due_date')[:5]
    )

    context = {
        'workspace_progress': workspace_progress,
        'done_tasks': done_tasks,
        'total_tasks': total_tasks,
        'active_projects_count': active_projects.count(),
        'active_projects_new': projects.filter(created_at__date__gte=week_ago).count(),
        'todo_tasks_count': todo_tasks.count(),
        'todo_tasks_new': tasks.filter(created_at__date__gte=week_ago).exclude(status=Task.Status.DONE).count(),
        'overdue_count': overdue_tasks.count(),
        'overdue_new': overdue_tasks.filter(due_date__gte=week_ago).count(),
        'members_count': members.count(),
        'members_new': members.filter(joined_at__date__gte=week_ago).count(),
        'activity': activity,
        'my_tasks': my_tasks,
        'today': today,
        'tomorrow': today + timedelta(days=1),
    }
    return render(request, 'projects/summary.html', context)


@login_required
def sprint_create(request, project_pk):
    project = get_user_project_or_404(request.user, project_pk)
    members_qs = User.objects.filter(team_memberships__workspace=project.workspace).distinct()

    if request.method == 'POST':
        form = SprintForm(request.POST, members_queryset=members_qs)
        if form.is_valid():
            sprint = form.save(commit=False)
            sprint.project = project
            sprint.save()
            form.save_m2m()
            messages.success(request, f"Le sprint « {sprint.name} » a été créé. Sélectionnez maintenant ses tâches depuis le Backlog.")
            return redirect('tasks:backlog', project_pk=project.pk)
    else:
        form = SprintForm(members_queryset=members_qs)

    context = {'form': form, 'project': project, 'is_edit': False}
    return render(request, 'projects/sprint_form.html', context)


@login_required
def sprint_edit(request, project_pk, pk):
    project = get_user_project_or_404(request.user, project_pk)
    sprint = get_object_or_404(Sprint, pk=pk, project=project)
    members_qs = User.objects.filter(team_memberships__workspace=project.workspace).distinct()

    if sprint.status != Sprint.Status.UPCOMING:
        messages.error(request, "Un sprint démarré ne peut plus être modifié — seul un sprint « À venir » peut l'être.")
        return redirect('projects:sprint_detail', project_pk=project.pk, pk=sprint.pk)

    if request.method == 'POST':
        form = SprintForm(request.POST, instance=sprint, members_queryset=members_qs)
        if form.is_valid():
            form.save()
            messages.success(request, f"Le sprint « {sprint.name} » a été mis à jour.")
            return redirect('projects:sprint_detail', project_pk=project.pk, pk=sprint.pk)
    else:
        form = SprintForm(instance=sprint, members_queryset=members_qs)

    context = {'form': form, 'project': project, 'is_edit': True, 'sprint': sprint}
    return render(request, 'projects/sprint_form.html', context)


@login_required
def sprint_detail(request, project_pk, pk):
    project = get_user_project_or_404(request.user, project_pk)
    sprint = get_object_or_404(Sprint, pk=pk, project=project)
    tasks = sprint.tasks.select_related('assignee').all()

    total = tasks.count()
    done = tasks.filter(status=Task.Status.DONE).count()
    late = tasks.exclude(status=Task.Status.DONE).filter(due_date__lt=date.today()).count()
    progress = round((done / total) * 100) if total else 0

    other_active = Sprint.objects.filter(project=project, status=Sprint.Status.ACTIVE).exclude(pk=sprint.pk).first()
    upcoming_sprints = Sprint.objects.filter(project=project, status=Sprint.Status.UPCOMING).exclude(pk=sprint.pk)
    unplanned_tasks = Task.objects.filter(project=project, sprint__isnull=True).exclude(status=Task.Status.DONE)

    context = {
        'project': project,
        'sprint': sprint,
        'tasks': tasks,
        'total': total,
        'done': done,
        'late': late,
        'progress': progress,
        'other_active': other_active,
        'upcoming_sprints': upcoming_sprints,
        'unplanned_tasks': unplanned_tasks,
        'today': date.today(),
    }
    return render(request, 'projects/sprint_detail.html', context)


@require_POST
@login_required
def sprint_start(request, project_pk, pk):
    project = get_user_project_or_404(request.user, project_pk)
    sprint = get_object_or_404(Sprint, pk=pk, project=project)

    if sprint.status != Sprint.Status.UPCOMING:
        messages.error(request, "Seul un sprint « À venir » peut être démarré.")
        return redirect('projects:sprint_detail', project_pk=project.pk, pk=sprint.pk)

    already_active = Sprint.objects.filter(project=project, status=Sprint.Status.ACTIVE).exclude(pk=sprint.pk).first()
    if already_active:
        messages.error(request, f"Impossible de démarrer ce sprint : « {already_active.name} » est déjà actif sur ce projet. Clôturez-le d'abord.")
        return redirect('projects:sprint_detail', project_pk=project.pk, pk=sprint.pk)

    sprint.status = Sprint.Status.ACTIVE
    sprint.save(update_fields=['status'])
    messages.success(request, f"Le sprint « {sprint.name} » est maintenant en cours.")
    return redirect('projects:sprint_detail', project_pk=project.pk, pk=sprint.pk)


@require_POST
@login_required
def sprint_cancel(request, project_pk, pk):
    project = get_user_project_or_404(request.user, project_pk)
    sprint = get_object_or_404(Sprint, pk=pk, project=project)
    sprint.status = Sprint.Status.CANCELLED
    sprint.save(update_fields=['status'])
    messages.success(request, f"Le sprint « {sprint.name} » a été annulé.")
    return redirect('tasks:backlog', project_pk=project.pk)


@login_required
def sprint_close(request, project_pk, pk):
    """Ecran de cloture d'un sprint : bilan + devenir des taches non terminees."""
    project = get_user_project_or_404(request.user, project_pk)
    sprint = get_object_or_404(Sprint, pk=pk, project=project)

    if sprint.status != Sprint.Status.ACTIVE:
        messages.error(request, "Seul un sprint « En cours » peut être clôturé.")
        return redirect('projects:sprint_detail', project_pk=project.pk, pk=sprint.pk)

    tasks = sprint.tasks.select_related('assignee').all()
    incomplete_tasks = tasks.exclude(status=Task.Status.DONE)
    done_tasks = tasks.filter(status=Task.Status.DONE)
    late_tasks = incomplete_tasks.filter(due_date__lt=date.today())
    next_sprints = Sprint.objects.filter(project=project, status=Sprint.Status.UPCOMING).exclude(pk=sprint.pk)

    if request.method == 'POST':
        for task in incomplete_tasks:
            action = request.POST.get(f'task_{task.pk}')
            if action == 'next_sprint':
                target_id = request.POST.get(f'target_sprint_{task.pk}')
                if target_id:
                    task.sprint_id = target_id
                    task.save(update_fields=['sprint'])
            elif action == 'backlog':
                task.sprint = None
                task.save(update_fields=['sprint'])
            elif action == 'cancel':
                task.status = Task.Status.CANCELLED
                task.save(update_fields=['status'])
            # action == 'reassign' : laisse la tache dans le sprint cloture, geree manuellement ensuite

        sprint.status = Sprint.Status.DONE
        sprint.closed_at = timezone.now()
        sprint.save(update_fields=['status', 'closed_at'])
        messages.success(request, f"Le sprint « {sprint.name} » a été clôturé.")
        return redirect('tasks:backlog', project_pk=project.pk)

    total = tasks.count()
    progress = round((done_tasks.count() / total) * 100) if total else 0
    objective_reached = progress == 100

    context = {
        'project': project,
        'sprint': sprint,
        'done_tasks': done_tasks,
        'incomplete_tasks': incomplete_tasks,
        'late_tasks': late_tasks,
        'progress': progress,
        'objective_reached': objective_reached,
        'next_sprints': next_sprints,
        'duration_days': (sprint.end_date - sprint.start_date).days,
    }
    return render(request, 'projects/sprint_close.html', context)