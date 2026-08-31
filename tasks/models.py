from django.db import models

# Create your models here.
#from django.db import models
from django.contrib.auth.models import User
from projects.models import Project, Sprint


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', 'À faire'
        IN_PROGRESS = 'in_progress', 'En cours'
        DONE = 'done', 'Terminé'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.TODO)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title