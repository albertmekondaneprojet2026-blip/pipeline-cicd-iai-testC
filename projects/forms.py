from django import forms
from .models import Project

ICON_CHOICES = [
    ('rocket', 'Fusée'),
    ('smartphone', 'Mobile'),
    ('trending-up', 'Croissance'),
    ('settings', 'Infrastructure'),
    ('users', 'Équipe'),
    ('briefcase', 'Business'),
    ('file-text', 'Documentation'),
    ('shield', 'Sécurité'),
]


class ProjectForm(forms.ModelForm):
    icon = forms.ChoiceField(choices=ICON_CHOICES, label='Icône', required=False)

    class Meta:
        model = Project
        fields = ['name', 'description', 'status', 'icon', 'lead', 'start_date', 'end_date']
        labels = {
            'name': 'Nom du projet',
            'description': 'Description',
            'status': 'Statut',
            'lead': 'Responsable',
            'start_date': 'Date de début',
            'end_date': 'Date de fin (facultative)',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Ex : Refonte site web'}),
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Décrivez le projet en quelques mots...'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, members_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if members_queryset is not None:
            self.fields['lead'].queryset = members_queryset
        self.fields['lead'].empty_label = 'Non assigné'
        self.fields['icon'].initial = self.instance.icon if self.instance and self.instance.pk else 'rocket'

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end and end < start:
            self.add_error('end_date', "La date de fin doit être postérieure à la date de début.")
        return cleaned
