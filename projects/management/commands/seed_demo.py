import random
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from workspaces.models import Workspace, TeamMember, UserPreference
from projects.models import Project, Sprint, Milestone, Goal
from tasks.models import Task


class Command(BaseCommand):
    help = "Cree un jeu de donnees de demonstration TaskFlow (utilisateur demo / demo1234)."

    def handle(self, *args, **options):
        random.seed(42)
        today = date.today()

        owner, created = User.objects.get_or_create(
            username='demo@taskflow.io',
            defaults={'email': 'demo@taskflow.io', 'first_name': 'Sarah', 'last_name': 'Martin'},
        )
        if created:
            owner.set_password('demo1234')
            owner.save()

        workspace, _ = Workspace.objects.get_or_create(
            owner=owner,
            defaults={'name': 'Mon Espace', 'description': "Espace de travail pour gerer vos projets et equipes."},
        )
        UserPreference.objects.get_or_create(user=owner)
        TeamMember.objects.get_or_create(user=owner, workspace=workspace, defaults={'role': 'admin', 'title': 'Chef de projet'})

        member_specs = [
            ('sophie.bernard', 'Sophie', 'Bernard', 'Developpeuse'),
            ('lucas.moreau', 'Lucas', 'Moreau', 'Designer'),
            ('camille.lefevre', 'Camille', 'Lefevre', 'Developpeuse'),
            ('antoine.petit', 'Antoine', 'Petit', 'Product Owner'),
            ('julie.richard', 'Julie', 'Richard', 'Analyste'),
        ]
        members = [owner]
        for username, first, last, title in member_specs:
            user, created = User.objects.get_or_create(
                username=f'{username}@taskflow.io',
                defaults={'email': f'{username}@taskflow.io', 'first_name': first, 'last_name': last},
            )
            if created:
                user.set_password('demo1234')
                user.save()
            UserPreference.objects.get_or_create(user=user)
            TeamMember.objects.get_or_create(user=user, workspace=workspace, defaults={'role': 'member', 'title': title})
            members.append(user)

        project_specs = [
            ('Refonte site web', "Nouvelle experience utilisateur et design moderne.", Project.Status.IN_PROGRESS, 'rocket'),
            ('Application mobile', "Developpement de la version iOS et Android.", Project.Status.PLANNED, 'smartphone'),
            ('Campagne marketing', "Lancement de la campagne Q2 sur les reseaux sociaux.", Project.Status.IN_PROGRESS, 'trending-up'),
            ('Infrastructure cloud', "Mise en place de l'environnement production.", Project.Status.PLANNED, 'settings'),
            ('Produit v2.0', "Ameliorations fonctionnelles et correction des bugs.", Project.Status.IN_REVIEW, 'users'),
        ]

        task_titles = [
            ("Concevoir la maquette de l'interface", 'Design', 'blue'),
            ("Developper l'API d'authentification", 'Backend', 'green'),
            ('Rediger la documentation utilisateur', 'Documentation', 'purple'),
            ('Tests de performance', 'Qualite', 'teal'),
            ('Deployer la version 1.0', 'Infrastructure', 'orange'),
            ('Creer le tableau de bord Analytics', 'Produit', 'blue'),
            ('Optimiser les performances de la base', 'Backend', 'green'),
            ('Preparer la presentation client', 'Marketing', 'orange'),
            ('Corriger les bugs signales', 'Support', 'red'),
            ('Finaliser les tests utilisateurs', 'Qualite', 'teal'),
        ]

        statuses = [Task.Status.TODO, Task.Status.IN_PROGRESS, Task.Status.IN_REVIEW, Task.Status.DONE]
        priorities = [Task.Priority.LOW, Task.Priority.MEDIUM, Task.Priority.HIGH]

        for name, description, status, icon in project_specs:
            project, _ = Project.objects.get_or_create(
                workspace=workspace, name=name,
                defaults={'description': description, 'status': status, 'icon': icon},
            )

            sprints = []
            phase_names = ['Conception', 'Developpement', 'Tests', 'Lancement']
            phase_objectives = [
                'Poser les bases visuelles et fonctionnelles du projet.',
                'Developper les fonctionnalites principales.',
                'Fiabiliser avant mise en production.',
                'Deployer et livrer la version finale.',
            ]
            phase_statuses = [Sprint.Status.DONE, Sprint.Status.ACTIVE, Sprint.Status.UPCOMING, Sprint.Status.UPCOMING]
            cursor = today - timedelta(days=20)
            for i, phase in enumerate(phase_names):
                start = cursor
                end = start + timedelta(days=14)
                sprint, _ = Sprint.objects.get_or_create(
                    project=project, name=phase,
                    defaults={
                        'start_date': start, 'end_date': end,
                        'status': phase_statuses[i],
                        'objective': phase_objectives[i],
                    },
                )
                if members:
                    sprint.members.add(*members[:3])
                sprints.append(sprint)
                cursor = end

            for i, (title, label, color) in enumerate(task_titles):
                Task.objects.get_or_create(
                    project=project, title=title,
                    defaults={
                        'sprint': random.choice(sprints),
                        'status': statuses[i % len(statuses)],
                        'priority': priorities[i % len(priorities)],
                        'label': label,
                        'label_color': color,
                        'due_date': today + timedelta(days=random.randint(-5, 30)),
                        'assignee': random.choice(members),
                    },
                )

        milestone_specs = [
            ('Lancement du MVP', today + timedelta(days=10), 'blue'),
            ('Version beta', today + timedelta(days=35), 'purple'),
            ('Lancement officiel', today + timedelta(days=60), 'green'),
            ('Evolution v1.0', today + timedelta(days=90), 'orange'),
        ]
        for i, (title, due, color) in enumerate(milestone_specs):
            Milestone.objects.get_or_create(workspace=workspace, title=title, defaults={'due_date': due, 'order': i, 'color': color})

        goal_specs = ['Satisfaction client 90%', 'Reduire les delais de livraison', 'Automatiser les tests', 'Lancer 2 nouveaux produits', 'Recruter 3 profils cles']
        for i, title in enumerate(goal_specs):
            Goal.objects.get_or_create(workspace=workspace, title=title, defaults={'order': i, 'is_completed': i < 3})

        self.stdout.write(self.style.SUCCESS(
            "Donnees de demonstration creees. Connectez-vous avec demo@taskflow.io / demo1234"
        ))