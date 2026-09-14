from django.db import models

# Create your models here.
#from django.db import models
from django.contrib.auth.models import User

class Workspace(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(
        blank=True,
        default="Espace de travail pour gerer vos projets et equipes.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_workspaces')

    def __str__(self):
        return self.name


class TeamMember(models.Model):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Membre'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    title = models.CharField(max_length=100, blank=True, default='Membre')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'workspace')

    def __str__(self):
        return f"{self.user.username} ({self.role}) - {self.workspace.name}"

    @property
    def initials(self):
        full_name = self.user.get_full_name() or self.user.username
        parts = [p for p in full_name.split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return full_name[:2].upper()


class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    notify_comments = models.BooleanField(default=True)
    notify_task_assigned = models.BooleanField(default=True)
    notify_project_updates = models.BooleanField(default=True)
    notify_due_date = models.BooleanField(default=True)
    two_factor_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"Preferences de {self.user.username}"
