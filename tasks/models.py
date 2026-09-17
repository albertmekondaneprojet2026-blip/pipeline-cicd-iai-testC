from django.db import models
from django.contrib.auth.models import User
from projects.models import Project, Sprint


class Task(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', 'A faire'
        IN_PROGRESS = 'in_progress', 'En cours'
        IN_REVIEW = 'in_review', 'En revue'
        DONE = 'done', 'Termine'
        CANCELLED = 'cancelled', 'Annulee'

    class Priority(models.TextChoices):
        LOW = 'low', 'Basse'
        MEDIUM = 'medium', 'Moyenne'
        HIGH = 'high', 'Haute'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.TODO)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    label = models.CharField(max_length=40, blank=True)
    label_color = models.CharField(max_length=20, default='blue')
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return self.title

    @property
    def assignee_initials(self):
        if not self.assignee:
            return '?'
        full_name = self.assignee.get_full_name() or self.assignee.username
        parts = [p for p in full_name.split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return full_name[:2].upper()
