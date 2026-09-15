from django.test import TestCase

# Create your tests here.
import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from workspaces.models import Workspace
from projects.models import Project
from tasks.models import Task


@pytest.fixture
def project(db):
    """Fixture : cree un utilisateur, un workspace et un projet reutilisables."""
    user = User.objects.create_user(username='testuser', password='testpass123')
    workspace = Workspace.objects.create(name='Test Workspace', owner=user)
    return Project.objects.create(workspace=workspace, name='Test Project')


@pytest.mark.django_db
def test_task_creation_defaults(project):
    """Une tache creee sans statut explicite doit avoir le statut par defaut 'todo'."""
    # Arrange : le fixture 'project' a deja prepare le contexte
    # Act
    task = Task.objects.create(project=project, title="Ma premiere tache")
    # Assert
    assert task.status == Task.Status.TODO
    assert task.is_blocked is False
    assert str(task) == "Ma premiere tache"


@pytest.mark.django_db
def test_task_status_choices_are_valid(project):
    """Le statut d'une tache doit toujours appartenir aux choix definis."""
    task = Task.objects.create(project=project, title="Tache statut", status=Task.Status.IN_PROGRESS)
    valid_statuses = [choice[0] for choice in Task.Status.choices]
    assert task.status in valid_statuses


@pytest.mark.django_db
def test_task_estimated_hours_can_be_null(project):
    """Le champ estimated_hours n'est pas obligatoire a la creation."""
    task = Task.objects.create(project=project, title="Tache sans estimation")
    assert task.estimated_hours is None

@pytest.fixture
def two_users_with_tasks(db):
    """Fixture : deux utilisateurs distincts, chacun avec son projet et sa tache."""
    user_a = User.objects.create_user(username='usera', password='pass123456')
    workspace_a = Workspace.objects.create(name='Workspace A', owner=user_a)
    project_a = Project.objects.create(workspace=workspace_a, name='Project A')
    task_a = Task.objects.create(project=project_a, title='Tache confidentielle A')

    user_b = User.objects.create_user(username='userb', password='pass123456')
    workspace_b = Workspace.objects.create(name='Workspace B', owner=user_b)
    project_b = Project.objects.create(workspace=workspace_b, name='Project B')
    task_b = Task.objects.create(project=project_b, title='Tache confidentielle B')

    return {
        'user_a': user_a, 'project_a': project_a, 'task_a': task_a,
        'user_b': user_b, 'project_b': project_b, 'task_b': task_b,
    }


@pytest.mark.django_db
def test_user_cannot_view_kanban_of_another_users_project(client, two_users_with_tasks):
    """Securite : le tableau Kanban d'un projet ne doit etre visible que par
    les membres de son propre espace de travail. Repond a la question
    'Comment verifier qu'un utilisateur ne voit pas les taches d'un autre ?'."""
    data = two_users_with_tasks
    client.login(username='usera', password='pass123456')

    # L'utilisateur A accede a SON projet : OK, et il voit sa tache
    response = client.get(reverse('tasks:kanban', kwargs={'project_pk': data['project_a'].pk}))
    assert response.status_code == 200
    assert b'Tache confidentielle A' in response.content

    # L'utilisateur A tente d'acceder au projet de B : refuse (404), aucune fuite de donnees
    response = client.get(reverse('tasks:kanban', kwargs={'project_pk': data['project_b'].pk}))
    assert response.status_code == 404
    assert b'Tache confidentielle B' not in response.content


@pytest.mark.django_db
def test_user_cannot_update_status_of_another_users_task(client, two_users_with_tasks):
    """Securite : impossible de modifier le statut d'une tache d'un autre espace
    de travail, meme via une requete POST directe sur l'URL."""
    data = two_users_with_tasks
    client.login(username='usera', password='pass123456')

    url = reverse('tasks:update_task_status', kwargs={'project_pk': data['project_b'].pk, 'pk': data['task_b'].pk})
    response = client.post(url, {'status': 'done'})

    assert response.status_code == 404
    data['task_b'].refresh_from_db()
    assert data['task_b'].status == Task.Status.TODO  # inchangee


@pytest.mark.django_db
def test_global_task_list_excludes_other_users_tasks(client, two_users_with_tasks):
    """Securite : la liste globale 'Taches' ne doit jamais melanger les taches
    de plusieurs espaces de travail differents."""
    data = two_users_with_tasks
    client.login(username='usera', password='pass123456')

    response = client.get(reverse('tasks:task_list'))

    assert response.status_code == 200
    assert b'Tache confidentielle A' in response.content
    assert b'Tache confidentielle B' not in response.content
