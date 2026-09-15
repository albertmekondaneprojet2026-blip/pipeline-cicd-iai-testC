from django.test import TestCase

# Create your tests here.
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from workspaces.models import Workspace
from projects.models import Project


@pytest.fixture
def logged_in_client(client, db):
    """Fixture : un client de test Django, deja authentifie."""
    user = User.objects.create_user(username='testuser', password='testpass123')
    workspace = Workspace.objects.create(name='Test Workspace', owner=user)
    project = Project.objects.create(workspace=workspace, name='Test Project')
    client.login(username='testuser', password='testpass123')
    return client, project


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
    from tasks.models import Task
    client, project = logged_in_client
    Task.objects.create(project=project, title="Tache 1", status='done')
    Task.objects.create(project=project, title="Tache 2", status='todo')

    response = client.get(reverse('projects:project_dashboard', kwargs={'pk': project.pk}))

    assert response.status_code == 200
    assert response.context['stats']['total'] == 2
    assert response.context['stats']['done'] == 1

@pytest.fixture
def other_user_project(db):
    """Fixture : un DEUXIEME utilisateur, avec son propre espace et projet."""
    user = User.objects.create_user(username='otheruser', password='otherpass123')
    workspace = Workspace.objects.create(name='Other Workspace', owner=user)
    project = Project.objects.create(workspace=workspace, name='Other Project')
    return project


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
