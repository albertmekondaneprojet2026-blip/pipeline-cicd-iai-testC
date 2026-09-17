from django import forms
from .models import Task

LABEL_COLOR_CHOICES = [
    ('blue', 'Bleu'), ('green', 'Vert'), ('purple', 'Violet'),
    ('orange', 'Orange'), ('red', 'Rouge'), ('teal', 'Sarcelle'), ('gray', 'Gris'),
]


class TaskForm(forms.ModelForm):
    label_color = forms.ChoiceField(choices=LABEL_COLOR_CHOICES, label='Couleur de l\'étiquette', required=False)

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assignee', 'priority', 'status',
            'sprint', 'due_date', 'label', 'label_color', 'estimated_hours', 'is_blocked',
        ]
        labels = {
            'title': 'Titre',
            'description': 'Description (facultative)',
            'assignee': 'Responsable',
            'priority': 'Priorité',
            'status': 'Statut',
            'sprint': 'Sprint',
            'due_date': 'Échéance (facultative)',
            'label': 'Étiquette (facultative)',
            'estimated_hours': 'Temps estimé (h)',
            'is_blocked': 'Tâche bloquée',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Ex : Concevoir la maquette de l\'interface'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'label': forms.TextInput(attrs={'placeholder': 'Ex : Design, Backend...'}),
        }

    def __init__(self, *args, project=None, members_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if members_queryset is not None:
            self.fields['assignee'].queryset = members_queryset
        self.fields['assignee'].empty_label = 'Non assignée'
        if project is not None:
            self.fields['sprint'].queryset = project.sprints.all()
        self.fields['sprint'].empty_label = 'Aucun (backlog)'
        self.fields['sprint'].required = False
