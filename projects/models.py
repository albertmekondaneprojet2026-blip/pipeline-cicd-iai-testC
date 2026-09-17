from django.db import models
from django.contrib.auth.models import User
from workspaces.models import Workspace


class Project(models.Model):
    class Status(models.TextChoices):
        PLANNED = 'planned', 'Planifie'
        IN_PROGRESS = 'in_progress', 'En cours'
        IN_REVIEW = 'in_review', 'En revision'
        DONE = 'done', 'Termine'

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='projects')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.IN_PROGRESS)
    icon = models.CharField(max_length=30, default='rocket')
    lead = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='led_projects', verbose_name='Responsable',
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class Sprint(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.name} ({self.project.name})"


class Milestone(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=150)
    due_date = models.DateField()
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=20, default='blue')

    class Meta:
        ordering = ['order', 'due_date']

    def __str__(self):
        return self.title


class Goal(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=150)
    is_completed = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
