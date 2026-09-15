from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import TeamMember, UserPreference
from .utils import get_user_workspace
from tasks.models import Task


@login_required
def team_view(request):
    workspace = get_user_workspace(request.user)
    members = TeamMember.objects.filter(workspace=workspace).select_related('user') if workspace else TeamMember.objects.none()

    for member in members:
        last_task = (
            Task.objects.filter(assignee=member.user, project__workspace=workspace)
            .select_related('project')
            .order_by('-updated_at')
            .first()
        )
        member.assigned_project = last_task.project.name if last_task else None

    context = {'workspace': workspace, 'members': members}
    return render(request, 'workspaces/team.html', context)


@login_required
def settings_view(request):
    workspace = get_user_workspace(request.user)
    preferences, _ = UserPreference.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            user = request.user
            user.first_name = request.POST.get('first_name', user.first_name).strip()
            user.last_name = request.POST.get('last_name', user.last_name).strip()
            user.email = request.POST.get('email', user.email).strip()
            user.save(update_fields=['first_name', 'last_name', 'email'])
            messages.success(request, "Votre profil a ete mis a jour.")

        elif form_type == 'workspace' and workspace:
            workspace.name = request.POST.get('name', workspace.name).strip() or workspace.name
            workspace.description = request.POST.get('description', workspace.description)
            workspace.save(update_fields=['name', 'description'])
            messages.success(request, "Les informations de l'espace de travail ont ete mises a jour.")

        elif form_type == 'notifications':
            preferences.notify_comments = bool(request.POST.get('notify_comments'))
            preferences.notify_task_assigned = bool(request.POST.get('notify_task_assigned'))
            preferences.notify_project_updates = bool(request.POST.get('notify_project_updates'))
            preferences.notify_due_date = bool(request.POST.get('notify_due_date'))
            preferences.save()
            messages.success(request, "Vos preferences de notification ont ete enregistrees.")

        elif form_type == 'security':
            preferences.two_factor_enabled = bool(request.POST.get('two_factor_enabled'))
            preferences.save()
            messages.success(request, "Vos parametres de securite ont ete mis a jour.")

        return redirect('workspaces:settings')

    context = {'workspace': workspace, 'preferences': preferences}
    return render(request, 'workspaces/settings.html', context)
