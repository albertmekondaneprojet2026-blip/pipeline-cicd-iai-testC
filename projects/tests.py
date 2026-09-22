from datetime import date, timedelta

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

from workspaces.models import Workspace
from projects.models import Project, Sprint
from tasks.models import Task


# =========================================================
# FIXTURES
# =========================================================

@pytest.fixture
def logged_in_client(client, db):
    """Fixture : un client de test Django, deja authentifie, avec son propre
    espace de travail et un projet."""
    user = User.objects.create_user(username='testuser', password='testpass123')
    workspace = Workspace.objects.create(name='Test Workspace', owner=user)
    project = Project.objects.create(workspace=workspace, name='Test Project')
    client.login(username='testuser', password='testpass123')
    return client, project


@pytest.fixture
def other_user_project(db):
    """Fixture : un DEUXIEME utilisateur, avec son propre espace et projet —
    sert a verifier qu'on ne peut jamais acceder aux donnees d'un autre."""
    user = User.objects.create_user(username='otheruser', password='otherpass123')
    workspace = Workspace.objects.create(name='Other Workspace', owner=user)
    project = Project.objects.create(workspace=workspace, name='Other Project')
    return project


@pytest.fixture
def project_with_sprint(logged_in_client):
    """Fixture : le projet de logged_in_client, avec un sprint 'A venir'."""
    client, project = logged_in_client
    sprint = Sprint.objects.create(
        project=project, name='Sprint 1', objective='Objectif test',
        start_date=date.today(), end_date=date.today() + timedelta(days=14),
    )
    return client, project, sprint


# =========================================================
# PROJETS — acces et securite
# =========================================================

@pytest.mark.django_db
def test_project_list_requires_authentication(client):
    """Un utilisateur non connecte doit etre redirige vers la page de connexion."""
    response = client.get(reverse('projects:project_list'))
    assert response.status_code == 302
    assert '/accounts/login/' in response.url


@pytest.mark.django_db
def test_project_list_accessible_when_logged_in(logged_in_client):
    """Un utilisateur connecte doit acceder normalement a la liste des projets."""
    client, project = logged_in_client
    response = client.get(reverse('projects:project_list'))
    assert response.status_code == 200
    assert project.name.encode() in response.content


@pytest.mark.django_db
def test_project_dashboard_shows_correct_stats(logged_in_client):
    """Le dashboard doit afficher des statistiques coherentes avec les taches reelles."""
    client, project = logged_in_client
    Task.objects.create(project=project, title="Tache 1", status='done')
    Task.objects.create(project=project, title="Tache 2", status='todo')

    response = client.get(reverse('projects:project_dashboard', kwargs={'pk': project.pk}))

    assert response.status_code == 200
    assert response.context['stats']['total'] == 2
    assert response.context['stats']['done'] == 1


@pytest.mark.django_db
def test_user_cannot_access_another_users_project_dashboard(logged_in_client, other_user_project):
    """Securite (autorisation) : un utilisateur connecte ne doit JAMAIS pouvoir
    consulter le dashboard d'un projet appartenant a un autre espace de travail,
    meme en connaissant son ID. On attend un 404 (et non les donnees du projet)."""
    client, _own_project = logged_in_client
    response = client.get(reverse('projects:project_dashboard', kwargs={'pk': other_user_project.pk}))
    assert response.status_code == 404
    assert other_user_project.name.encode() not in response.content


@pytest.mark.django_db
def test_project_list_only_shows_own_projects(logged_in_client, other_user_project):
    """Securite (autorisation) : la liste des projets ne doit afficher que
    ceux de l'espace de travail de l'utilisateur connecte."""
    client, own_project = logged_in_client
    response = client.get(reverse('projects:project_list'))
    assert own_project.name.encode() in response.content
    assert other_user_project.name.encode() not in response.content


# =========================================================
# PROJETS — CRUD (Phase 1)
# =========================================================

@pytest.mark.django_db
def test_project_create_view(logged_in_client):
    """Le formulaire de creation de projet doit fonctionner de bout en bout."""
    client, _own_project = logged_in_client
    response = client.post(reverse('projects:project_create'), {
        'name': 'Nouveau projet test',
        'description': 'Une description',
        'status': 'planned',
        'icon': 'rocket',
    })
    assert response.status_code == 302
    assert Project.objects.filter(name='Nouveau projet test').exists()


@pytest.mark.django_db
def test_project_edit_view(logged_in_client):
    client, project = logged_in_client
    response = client.post(reverse('projects:project_edit', kwargs={'pk': project.pk}), {
        'name': 'Nom modifie',
        'description': project.description,
        'status': project.status,
        'icon': project.icon,
    })
    assert response.status_code == 302
    project.refresh_from_db()
    assert project.name == 'Nom modifie'


@pytest.mark.django_db
def test_project_archive_view(logged_in_client):
    client, project = logged_in_client
    assert project.is_archived is False
    response = client.post(reverse('projects:project_archive', kwargs={'pk': project.pk}))
    assert response.status_code == 302
    project.refresh_from_db()
    assert project.is_archived is True


@pytest.mark.django_db
def test_cannot_edit_another_users_project(logged_in_client, other_user_project):
    """Securite : impossible de modifier le projet d'un autre espace de travail."""
    client, _own_project = logged_in_client
    response = client.post(reverse('projects:project_edit', kwargs={'pk': other_user_project.pk}), {
        'name': 'Piratage', 'status': 'planned', 'icon': 'rocket',
    })
    assert response.status_code == 404
    other_user_project.refresh_from_db()
    assert other_user_project.name != 'Piratage'


# =========================================================
# SPRINTS — cycle de vie (Phase 2)
# =========================================================

@pytest.mark.django_db
def test_sprint_create_view(logged_in_client):
    """Un sprint nouvellement cree doit demarrer avec le statut 'A venir'."""
    client, project = logged_in_client
    response = client.post(reverse('projects:sprint_create', kwargs={'project_pk': project.pk}), {
        'name': 'Sprint 1', 'objective': 'Objectif test',
        'start_date': date.today(), 'end_date': date.today() + timedelta(days=14),
    })
    assert response.status_code == 302
    sprint = Sprint.objects.get(project=project, name='Sprint 1')
    assert sprint.status == Sprint.Status.UPCOMING


@pytest.mark.django_db
def test_sprint_start_view(project_with_sprint):
    client, project, sprint = project_with_sprint
    response = client.post(reverse('projects:sprint_start', kwargs={'project_pk': project.pk, 'pk': sprint.pk}))
    assert response.status_code == 302
    sprint.refresh_from_db()
    assert sprint.status == Sprint.Status.ACTIVE


@pytest.mark.django_db
def test_only_one_active_sprint_per_project(project_with_sprint):
    """Regle metier de la spec : un seul sprint actif par projet a la fois."""
    client, project, sprint = project_with_sprint
    client.post(reverse('projects:sprint_start', kwargs={'project_pk': project.pk, 'pk': sprint.pk}))

    second_sprint = Sprint.objects.create(
        project=project, name='Sprint 2',
        start_date=date.today(), end_date=date.today() + timedelta(days=14),
    )
    response = client.post(reverse('projects:sprint_start', kwargs={'project_pk': project.pk, 'pk': second_sprint.pk}))
    assert response.status_code == 302
    second_sprint.refresh_from_db()
    assert second_sprint.status == Sprint.Status.UPCOMING  # inchange, demarrage refuse


@pytest.mark.django_db
def test_sprint_close_returns_tasks_to_backlog(project_with_sprint):
    """A la cloture, les taches non terminees suivent la decision (backlog par
    defaut) et aucune n'est jamais supprimee."""
    client, project, sprint = project_with_sprint
    sprint.status = Sprint.Status.ACTIVE
    sprint.save()
    task = Task.objects.create(project=project, sprint=sprint, title='Tache non finie')

    response = client.post(
        reverse('projects:sprint_close', kwargs={'project_pk': project.pk, 'pk': sprint.pk}),
        {f'task_{task.pk}': 'backlog'},
    )
    assert response.status_code == 302
    sprint.refresh_from_db()
    task.refresh_from_db()
    assert sprint.status == Sprint.Status.DONE
    assert sprint.closed_at is not None
    assert task.sprint is None  # renvoyee au backlog
    assert Task.objects.filter(pk=task.pk).exists()  # jamais supprimee


@pytest.mark.django_db
def test_cannot_edit_sprint_after_it_started(project_with_sprint):
    """Seul un sprint 'A venir' peut etre modifie (regle de la spec 9.7)."""
    client, project, sprint = project_with_sprint
    sprint.status = Sprint.Status.ACTIVE
    sprint.save()

    response = client.post(reverse('projects:sprint_edit', kwargs={'project_pk': project.pk, 'pk': sprint.pk}), {
        'name': 'Nom pirate', 'start_date': sprint.start_date, 'end_date': sprint.end_date,
    })
    assert response.status_code == 302
    sprint.refresh_from_db()
    assert sprint.name != 'Nom pirate'


@pytest.mark.django_db
def test_cannot_manage_sprint_of_another_users_project(logged_in_client, other_user_project):
    """Securite : impossible de creer un sprint dans le projet d'un autre espace."""
    client, _own_project = logged_in_client
    response = client.post(reverse('projects:sprint_create', kwargs={'project_pk': other_user_project.pk}), {
        'name': 'Intrusion', 'start_date': '2026-01-01', 'end_date': '2026-01-14',
    })
    assert response.status_code == 404