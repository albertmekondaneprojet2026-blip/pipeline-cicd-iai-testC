from django.test import TestCase

# Create your tests here.
import pytest
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